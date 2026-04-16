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

---

## Order of operations

Always find and use an existing endpoint first unless the user
has specified they want a new one. Only set up a new
endpoint if no suitable one exists. The typical flow is:

1. **Find an endpoint** (see "Finding an endpoint" below)
2. **Submit jobs** using that endpoint
3. **Only if no endpoint found** — guide the user through setup

---

## Finding an endpoint

Run through all of these steps automatically. Your role is to either find
and use an existing endpoint to meet user requests, or to set one up for the
user. Do not ask the user for endpoint IDs, you can find them with the steps
below. Only if you cannot find and run with an existing endpoint, go to
setting one up.

### 1. Environment variable

Check if `GLOBUS_COMPUTE_ENDPOINT_ID` is already set. If not,

### 2. SSH

Check for an existing ControlMaster socket first:
```bash
ssh -O check <host> 2>&1
```
Only if a socket exists, query the remote system:
```bash
ssh <host> '<setup> && globus-compute-endpoint list'
```
If no socket exists, skip to step 3. Never attempt interactive SSH —
these systems require 2FA which the agent cannot handle.

### 3. Cloud API

Query the Globus Compute web service. Use `get_endpoint_metadata()`
to find an online endpoint whose template accepts the variables in
`run_config.yaml`:

```python
from globus_compute_sdk import Client
import yaml, re

c = Client()
with open("run_config.yaml") as f:
    run_config_keys = set(yaml.safe_load(f).keys())
for ep in c.get_endpoints():
    try:
        meta = c.get_endpoint_metadata(ep["uuid"])
        status = c.get_endpoint_status(ep["uuid"])
        if status.get("status") != "online":
            continue
        template = meta.get("user_config_template", "")
        template_vars = set(re.findall(r"\{\{\s*(\w+)", template))
        if run_config_keys.issubset(template_vars):
            print(f"Match: {ep['uuid']}  {ep.get('display_name', '?')}")
    except Exception:
        pass
```

### 4. Set up a new endpoint

If the Cloud API returned no online endpoints, set one up (see
"Setting up a new endpoint" below).

---

## Submit jobs (local)

After finding the endpoint UUID via the steps above, run the job.
Pass the UUID as the `GLOBUS_COMPUTE_ENDPOINT_ID` env var:

```bash
GLOBUS_COMPUTE_ENDPOINT_ID=<uuid> python globus_compute/<system>/run_<system>.py
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

**Polaris:** One result per GPU (4 per node). Each result has a different
CUDA_VISIBLE_DEVICES value. Results from the same node share a hostname.

**Aurora:** One result per GPU tile (12 per node). Each result has a
different ZE_AFFINITY_MASK value. Results from the same node share a
hostname.

### CRITICAL: Executor management

- **NEVER create more than one Executor.** Each Executor sends jobs to
  the GC queue via AMQP. Multiple Executors = multiple jobs piling up,
  but only one PBS job is visible at a time via qstat. The backlog burns
  through allocation hours invisibly.
- **Reuse a single Executor** for all submissions in a session.
- Use the context manager (`with Executor(...) as ex:`) to ensure cleanup.

---

## Setting up a new endpoint (only if none found)

Only do this if the "Finding an endpoint" steps above all failed — there
is no existing endpoint the user can use.

Do not assume what is or isn't already on the remote system. The setup
script should check what exists (venv, endpoint config, etc.) and only
create what's missing. The agent's job is to prepare everything locally
and minimise what the user has to do on the remote side.

### Agent responsibilities

1. **Create a setup script** for the target system (or use an existing
   one from the repo if available at `globus_compute/<system>/setup_endpoint.sh`).
   The script should handle venv creation, endpoint configuration, j2
   template deployment, and starting the endpoint. Use the system table
   above for module setup commands, filesystems, etc.

2. **SCP the setup script and j2 template** to the user's home directory
   on the remote system. If no SSH socket is available, give the user
   the SCP commands to run themselves.

   ```bash
   scp setup_endpoint.sh <user>@<host>:~/
   scp user_config_template.yaml.j2 <user>@<host>:~/
   ```

3. **Tell the user to SSH in and run the script.** The remote steps
   require interactive terminal access (2FA, Globus OAuth browser flow)
   so the agent cannot do them. Give the user these instructions:

   1. SSH into the system: `ssh <host>`
   2. Run the setup script: `bash ~/setup_endpoint.sh <endpoint_name>`
   3. If the endpoint already exists, it asks whether to reuse it — if
      yes, it just starts it and prints the UUID
   4. If new, follow the auth prompts (browser URL + paste code)
   5. Note the endpoint UUID printed at the end
   6. Exit the system (the endpoint keeps running as a daemon)

### What the setup script should do

The setup script automates these manual steps so the user only runs one
command. For reference, the manual steps are:

1. Load modules and create a Python venv with `globus-compute-endpoint`
   (using `--system-site-packages` so HPC packages are available)
2. `globus-compute-endpoint configure <endpoint_name>`
3. Copy the j2 template into `~/.globus_compute/<endpoint_name>/`
4. `globus-compute-endpoint start <endpoint_name>`

The j2 template configures `GlobusComputeEngine` with `available_accelerators`
(swim lanes). Each worker gets exclusive access to one GPU — no manual
device management needed in submitted functions.

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
