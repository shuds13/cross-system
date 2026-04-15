---
name: globus-compute-endpoint
description: >
  Set up and test a Globus Compute user endpoint on ALCF Polaris or Aurora with
  accelerator-pinned GPU workers (GlobusComputeEngine). Covers venv creation,
  endpoint configuration, j2 template deployment, and running the GPU smoke test.
---

# Setup Globus Compute Endpoint

Set up a user-managed Globus Compute endpoint with GlobusComputeEngine
(accelerator pinning — each worker gets exclusive access to one GPU).

## Supported systems

| System | GPUs/node | Accelerator type | Scheduler |
|--------|-----------|------------------|-----------|
| Polaris (ALCF) | 4 (NVIDIA A100) | CUDA | PBS |
| Aurora (ALCF) | 12 (Intel GPU tiles) | Intel XPU | PBS |

## CRITICAL: Interactive steps

SSH and Globus auth require user interaction. Tell the user to run these
commands themselves — do NOT attempt to run them via tool calls.

## Step 1: On HPC system — create venv and configure endpoint

Tell the user to SSH to the target system and run:

**Polaris**
```bash
module use /soft/modulefiles && module load conda && conda activate
mkdir -p ~/venvs && python -m venv ~/venvs/gcompute --system-site-packages
source ~/venvs/gcompute/bin/activate
pip install globus-compute-endpoint
globus-compute-endpoint configure polaris
```

**Aurora**
```bash
module load frameworks
mkdir -p ~/venvs && python -m venv ~/venvs/gcompute --system-site-packages
source ~/venvs/gcompute/bin/activate
pip install globus-compute-endpoint globus-compute-sdk
globus-compute-endpoint configure aurora_test
```

## Step 2: Deploy the j2 template

Copy the template from this repo to the HPC system. You CAN run scp:

**Polaris**
```bash
scp globus_compute/polaris/globus_config_file/user_config_template.yaml.j2 <username>@polaris.alcf.anl.gov:~/.globus_compute/polaris/
```

**Aurora**
```bash
scp globus_compute/aurora/globus_config_file/user_config_template.yaml.j2 <username>@aurora.alcf.anl.gov:~/.globus_compute/aurora_test/
```

The template configures GlobusComputeEngine with `available_accelerators`, which
pins each worker to a specific GPU. This is different from the simple launcher
approach where tasks must manually manage device assignment.

## Step 3: Start the endpoint

Tell the user to run on the HPC system:

```bash
source ~/venvs/gcompute/bin/activate
globus-compute-endpoint start <endpoint_name>
```

They should copy the endpoint UUID from the output.

## Step 4: Configure and run the smoke test

On the laptop/front-end:

1. Set `account` in `globus_compute/<system>/run_config.yaml` to the user's allocation
2. Set the endpoint UUID:
   ```bash
   export GLOBUS_COMPUTE_ENDPOINT_ID=<uuid-from-step-3>
   ```
3. Run the test:
   ```bash
   cd globus_compute/<system> && python run_<system>.py
   ```

**Polaris expected output:** 4 results, each with a different CUDA_VISIBLE_DEVICES (0-3),
all on the same hostname.

**Aurora expected output:** 12 results per node, each with a different ZE_AFFINITY_MASK,
hostnames matching the number of requested nodes.

## Step 5: Verify

On the HPC system, check queue:

```bash
qstat -fu $USER
```

Should show one PBS job (not multiple). If multiple jobs keep appearing, workers
are crashing — see `globus_compute/troubleshooting.md`.

## Key config details

| | Polaris | Aurora |
|---|---|---|
| GPUs/node | 4 (A100) | 12 (Intel tiles) |
| Filesystems | home:eagle | home:flare |
| Module setup | `module use /soft/modulefiles && module load conda && conda activate` | `module load frameworks` |
| Python | 3.12 | 3.12 |
| Device env var | CUDA_VISIBLE_DEVICES | ZE_AFFINITY_MASK |
| Venv | ~/venvs/gcompute | ~/venvs/gcompute |
| worker_init includes | venv activate, TMPDIR=/tmp | venv activate, TMPDIR=/tmp |

## Troubleshooting

See `globus_compute/troubleshooting.md` for common issues:
- `globus-compute-endpoint: command not found` — venv not activated or package in ~/.local instead of venv
- `AF_UNIX path too long` — missing `export TMPDIR=/tmp` in worker_init
- Jobs exit immediately — check `~/.globus_compute/uep.*/submit_scripts/*.stderr`
- Blocks retrying every ~60s — workers crashing, stop endpoint and check stderr
- Script hanging — job finished but workers failed, check logs

## Endpoint management

```bash
globus-compute-endpoint list
globus-compute-endpoint start <endpoint_name>
globus-compute-endpoint stop <endpoint_name>
globus-compute-endpoint restart <endpoint_name>
```

## Cleanup

```bash
globus-compute-endpoint stop <endpoint_name>
qdel $(qselect -u $USER)
```
