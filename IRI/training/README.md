# ezpz Distributed Training via IRI

Runs `ezpz.examples.test` (MNIST MLP) across ALCF and NERSC using the amsc-client SDK.
Environments are pre-staged on each facility so jobs start instantly with no runtime installs.

## Setup (once per facility)

**NERSC:**
```
bash setup_nersc_env.sh
```
Creates a venv at `$SCRATCH/amsc-envs/ezpz` with ezpz and mpi4py installed.

**ALCF:** setup script not yet created — see `envs.yaml` for the expected venv path.

After setup, update `envs.yaml` if your venv landed at a different path.

## Submit

```
# Using ezpz launch
python submit_job_ezpz.py nersc --account <account> --username <username>

# Using torchrun
python submit_job_torchrun.py nersc --account <account> --username <username>
```

Both scripts read `envs.yaml` for the venv path and modules to load.

## Files

| File | Purpose |
|------|---------|
| `envs.yaml` | Catalog of pre-staged venv paths and modules per facility |
| `setup_nersc_env.sh` | One-time venv setup script for Perlmutter login node |
| `submit_job_ezpz.py` | Submit using `ezpz launch` (SLURM-native srun launcher) |
| `submit_job_torchrun.py` | Submit using `torchrun` (avoids srun step overhead) |

## Requirements (local)

```
pip install amsc-client pyyaml
```
