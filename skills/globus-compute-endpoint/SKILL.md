---
name: globus-compute-endpoint
description: >
  Set up, submit jobs to, and manage a Globus Compute endpoint on a remote
  HPC system. Covers endpoint creation, job submission, result collection,
  endpoint monitoring, log checking, and debugging.
---

# Globus Compute — Endpoint Setup and Usage

Set up user-managed Globus Compute endpoints with GlobusComputeEngine
(accelerator pinning — each worker gets exclusive access to one GPU).
Submit jobs locally, manage and debug endpoints via SSH.

## Supported systems

| | Polaris | Aurora |
|---|---|---|
| SSH host | `polaris` (or `polaris.alcf.anl.gov`) | `aurora` (or `aurora.alcf.anl.gov`) |
| GPUs/node | 4 (NVIDIA A100) | 12 (Intel GPU tiles) |
| Device env var | CUDA_VISIBLE_DEVICES | ZE_AFFINITY_MASK |
| Scheduler | PBS | PBS |
| Module setup | `module use /soft/modulefiles && module load conda && conda activate` | `module load frameworks` |
| Filesystems | home:eagle | home:flare |
| cpus_per_node | 64 | 208 |

## What the user does (on the HPC system)

These steps require interactive terminal access (2FA, Globus OAuth browser
flow). The user does them once per endpoint. Give the user these
instructions — do NOT attempt them via non-interactive SSH.

### Setup script (recommended)

Each system has a setup script at `globus_compute/<system>/setup_endpoint.sh`
that automates venv creation, login, configure, j2 deploy, and start.

1. SSH into the system: `ssh <host>`
2. Run the setup script: `bash setup_endpoint.sh <endpoint_name>`
3. Follow the auth prompts (browser URL + paste code)
4. Note the endpoint UUID printed at the end
5. Exit the system (the endpoint keeps running as a daemon)

### Manual steps (if not using setup script)

**1. SSH into the HPC system**

```
ssh <host>
```

**2. Create a Python venv with globus-compute-endpoint**

Polaris:
```
module use /soft/modulefiles && module load conda && conda activate && mkdir -p ~/venvs && python -m venv ~/venvs/gcompute --system-site-packages && source ~/venvs/gcompute/bin/activate && pip install globus-compute-endpoint
```

Aurora:
```
module load frameworks && mkdir -p ~/venvs && python -m venv ~/venvs/gcompute --system-site-packages && source ~/venvs/gcompute/bin/activate && pip install globus-compute-endpoint globus-compute-sdk
```

**3. Log in to Globus**

```
globus-compute-endpoint login
```

This opens a browser auth flow. Complete it once — tokens persist.

**4. Configure the endpoint**

```
globus-compute-endpoint configure <endpoint_name>
```

**5. Deploy the j2 template**

Copy the template into the endpoint config directory. Templates are in
this repo at `globus_compute/<system>/globus_config_file/`.

If on the HPC system with access to the repo, copy directly. Otherwise
from a local terminal:
```
scp globus_compute/<system>/globus_config_file/user_config_template.yaml.j2 <user>@<host>:~/.globus_compute/<endpoint_name>/
```

The template configures `GlobusComputeEngine` with `available_accelerators`
(swim lanes). Each worker gets exclusive access to one GPU — no manual
device management needed in submitted functions.

**6. Start the endpoint**

```
source ~/venvs/gcompute/bin/activate && globus-compute-endpoint start <endpoint_name>
```

Note the **endpoint UUID** from the output — needed for job submission.

The endpoint daemonizes (forks to background). It survives SSH disconnection
but NOT ctrl-c. The user can log out after starting it.

### SSH ControlMaster (for agent access)

The user's `~/.ssh/config` needs ControlMaster with ControlPersist so the
agent can reuse the authenticated SSH connection:

```
Host <host>
    ControlMaster auto
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlPersist yes
```

The user SSHs in once (handles 2FA), then exits. The socket stays alive
for the agent to use.

---

## What the agent does (from the local side)

Everything below can be done non-interactively. The agent needs:
- The endpoint UUID (from setup above)
- SSH ControlMaster socket active
- `globus-compute-sdk` installed locally

## Submit jobs (local)

Use `globus_compute/<system>/run_<system>.py` with the endpoint UUID:

```bash
export GLOBUS_COMPUTE_ENDPOINT_ID=<uuid>
cd globus_compute/<system>
python run_<system>.py
```

Or submit programmatically:
```python
import json
from globus_compute_sdk import Executor

with Executor(endpoint_id="<uuid>", user_endpoint_config=config) as ex:
    futures = [ex.submit(func, *args) for args in arg_list]
    results = [f.result() for f in futures]

with open("results.json", "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
```

The `user_endpoint_config` dict fills Jinja2 variables in the j2 template
(account, queue, walltime, num_nodes).

**Always save results to a file** — one JSON object per line (JSONL).

### Expected output

**Polaris (1 node):** 4 results, each with a different CUDA_VISIBLE_DEVICES
(0–3), all on the same hostname.

**Aurora (1 node):** 12 results, each with a different ZE_AFFINITY_MASK,
all on the same hostname.

### CRITICAL: Executor management

- **NEVER create more than one Executor.** Each Executor sends jobs to
  the GC queue via AMQP. Multiple Executors = multiple jobs piling up,
  but only one PBS job is visible at a time via qstat. The backlog burns
  through allocation hours invisibly.
- **Reuse a single Executor** for all submissions in a session.
- Use the context manager (`with Executor(...) as ex:`) to ensure cleanup.

## Endpoint management (via SSH)

All commands require the module setup and venv activation prefix.
Use `<setup>` as shorthand for: `<module_setup> && source ~/venvs/gcompute/bin/activate`

```bash
# List endpoints
ssh <host> '<setup> && globus-compute-endpoint list'

# Stop
ssh <host> '<setup> && globus-compute-endpoint stop <endpoint_name>'

# Restart
ssh <host> '<setup> && globus-compute-endpoint restart <endpoint_name>'

# Start (only if user has already authenticated — will fail if auth needed)
ssh <host> '<setup> && globus-compute-endpoint start <endpoint_name>'
```

## Verify

Check the PBS queue on the remote system:
```bash
ssh <host> 'qstat -fu $USER'
```

Should show one PBS job (not multiple). If multiple jobs keep appearing,
workers are crashing — see troubleshooting below.

## Debugging (via SSH)

When things go wrong, check these logs on the remote system:

```bash
# Endpoint manager log
ssh <host> 'cat ~/.globus_compute/<endpoint_name>/endpoint.log | tail -30'

# UEP interchange log
ssh <host> 'cat ~/.globus_compute/uep.*/endpoint.log | tail -30'

# Worker stderr (most useful for startup failures)
ssh <host> 'cat ~/.globus_compute/uep.*/submit_scripts/*.stderr 2>/dev/null | tail -40'

# Worker stdout
ssh <host> 'cat ~/.globus_compute/uep.*/submit_scripts/*.stdout 2>/dev/null | tail -20'

# PBS queue status
ssh <host> 'qstat -fu $USER'

# Rendered submit script (what actually runs on compute nodes)
ssh <host> 'cat ~/.globus_compute/uep.*/submit_scripts/parsl.GlobusComputeEngine-HighThroughputExecutor.block-0.*[0-9]'
```

### Common issues

**Workers crash on startup (blocks retrying every ~60s):**
Stop the endpoint immediately to halt the retry loop:
```bash
ssh <host> '<setup> && globus-compute-endpoint stop <endpoint_name>'
```
Check stderr, fix the j2 template, re-deploy via SCP, restart.

**`globus-compute-endpoint: command not found` on compute node:**
The `worker_init` in the j2 must activate the same venv. Check it includes
`source ~/venvs/gcompute/bin/activate`.

**`globus-compute-endpoint: command not found` locally (on login node):**
Modules must be loaded before activating the venv. The `--system-site-packages`
venv depends on packages from the module environment.

**`OSError: AF_UNIX path too long`:**
Add `export TMPDIR=/tmp` to `worker_init` in the j2 template.

**Script hangs — no results:**
Job may have finished but workers failed. Check stderr and queue status.

**Multiple PBS jobs appearing:**
Workers crashing causes parsl to allocate new blocks. Stop endpoint, fix
issue, restart. Clean up:
```bash
ssh <host> 'qdel $(qselect -u $USER)'
```

**Temp files in home directory:**
Parsl creates `cmd_parsl.*.sh` and `parsl.*.nodes` in `$HOME` per block.
Clean up after jobs finish:
```bash
ssh <host> 'rm -f ~/cmd_parsl.GlobusComputeEngine-* ~/parsl.GlobusComputeEngine-*'
```

## Cleanup

```bash
ssh <host> '<setup> && globus-compute-endpoint stop <endpoint_name>'
ssh <host> 'qdel $(qselect -u $USER)'
```

## Safety rules for autonomous operation

- **Read freely** — check any logs, list files, inspect configs.
- **Only modify via defined operations** — start/stop/restart endpoints,
  deploy j2 templates, clean up temp files. No arbitrary file deletion
  or modification on the remote system.
- **Monitor job count** — if multiple PBS jobs keep appearing and dying,
  stop the endpoint. Do not let retry loops continue.
- **Single Executor** — never create more than one. Track submissions.
- **Check before submitting** — verify the endpoint is running before
  attempting job submission.
