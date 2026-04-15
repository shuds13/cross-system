# Troubleshooting — Globus Compute User Endpoints

## `globus-compute-endpoint: command not found`

The endpoint binary isn't on PATH. Ensure you activated the venv where it's installed:

```bash
source ~/venvs/gcompute/bin/activate
which globus-compute-endpoint
```

If `pip install globus-compute-endpoint` says "Requirement already satisfied" but the
command still isn't found, the package is installed elsewhere (e.g. `~/.local`). Remove
the stale install and reinstall in the venv:

```bash
pip uninstall -y globus-compute-endpoint globus-compute-sdk
pip install globus-compute-endpoint
```

Also ensure `worker_init` in the j2 template activates the same venv, since workers on
compute nodes need the binary too.

## `OSError: AF_UNIX path too long`

The UEP working directory path exceeds the 108-character Unix socket limit. Add
`export TMPDIR=/tmp` to `worker_init` in the j2 template.

## Job exits immediately

Check the worker stderr for the failing block:

```bash
cat ~/.globus_compute/uep.*/submit_scripts/*.stderr | tail -40
```

Common causes:
- `worker_init` command fails (bad module load, missing venv)
- `globus-compute-endpoint` not found on compute node
- Socket path too long (see above)

## Blocks keep retrying (new block allocated every ~60s)

Workers are crashing on startup and parsl keeps scaling out replacement blocks. Each
block is a new batch job. Stop the endpoint to halt the cycle:

```bash
globus-compute-endpoint stop <endpoint_name>
```

Check stderr (see above), fix the j2, and restart.

## Script hangs — no results returned

The batch job may have finished but workers failed before processing any tasks. Check:

```bash
# Queue status (PBS / SLURM)
qstat -fu $USER       # PBS (Polaris, Aurora)
squeue -u $USER       # SLURM (Perlmutter)

# Worker stderr
cat ~/.globus_compute/uep.*/submit_scripts/*.stderr | tail -40

# Endpoint log
tail -30 ~/.globus_compute/uep.*/endpoint.log
```

## Endpoint status shows offline

Restart it on the HPC system:

```bash
globus-compute-endpoint restart <endpoint_name>
```

## Multiple batch jobs appearing

If `max_blocks` in the j2 is set higher than 1, or if workers keep failing (causing
retries), you may see multiple jobs. To clean up:

```bash
# Stop the endpoint
globus-compute-endpoint stop <endpoint_name>

# Delete all your jobs
qdel $(qselect -u $USER)    # PBS (Polaris, Aurora)
scancel -u $USER             # SLURM (Perlmutter)
```

## Checking the actual submit script

The rendered submit script shows exactly what runs on the compute node:

```bash
cat ~/.globus_compute/uep.*/submit_scripts/parsl.GlobusComputeEngine-HighThroughputExecutor.block-0.*[0-9]
```

## Useful log locations

| Log | Path |
|-----|------|
| Endpoint manager | `~/.globus_compute/<endpoint_name>/endpoint.log` |
| UEP interchange | `~/.globus_compute/uep.*/endpoint.log` |
| Submit scripts | `~/.globus_compute/uep.*/submit_scripts/` |
| Worker stderr | `~/.globus_compute/uep.*/submit_scripts/*.stderr` |
| Worker stdout | `~/.globus_compute/uep.*/submit_scripts/*.stdout` |
