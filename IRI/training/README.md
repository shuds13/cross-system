# Distributed Training via IRI

Runs `ezpz.examples.test` (MNIST MLP) across ALCF and NERSC using the amsc-client SDK.
Environments are pre-staged on each facility, and referenced by entry in `envs.yaml`.

## Setup (once per facility)

**NERSC:**
```
bash setup_nersc_perlmutter_env/ezpz.sh
```

**ALCF (Polaris):**
```
bash setup_alcf_polaris_env/ezpz.sh
```


## Submit

```
# Using ezpz launch
python submit_job_ezpz.py <facility> --account <account> --username <username> --nodes <num_nodes>

# Using torchrun
python submit_job_torchrun.py <facility> --account <account> --username <username> --nodes <num_nodes>
```

Both scripts read `envs.yaml` for the venv path and modules to load. `<facility>` is `alcf` or `nersc`.

## Files

| File | Purpose |
|------|---------|
| `envs.yaml` | Catalog of pre-staged venv paths and modules per facility |
| `setup_nersc_perlmutter_env/ezpz.sh` | One-time venv setup script for Perlmutter login node |
| `submit_job_ezpz.py` | Submit using `ezpz launch` |
| `submit_job_torchrun.py` | Submit using `torchrun` |

## Requirements (local)

```
pip install amsc-client pyyaml
```
