# IRI Cross-Facility Examples

Python script examples for interacting with IRI-compliant facilities (ALCF, NERSC) using the `amsc-client` SDK.

See also: [AmSC Client Tutorial Notebooks](https://github.com/amsc-interfaces/amsc-client-tutorial)

## Setup

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Explore resources (no auth required)

```
python submit_job.py alcf --explore-only
python submit_job.py nersc --explore-only
```

### Submit a job

```
python submit_job.py alcf --account <your-project> --username <you>
python submit_job.py nersc --account <your-project> --username <you>
```

Job submission triggers a Globus login in your browser on first use. The script submits a hello-world job, monitors until completion, then reads stdout via the filesystem API.

Use `--monitor-timeout 0` to submit without waiting. If the job doesn't complete within the monitoring window, the script prints a command to read output later:

```
python submit_job.py alcf --read-output /home/<you>/iri_job_outputs/iri-run-20260417-153000.stdout
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--executable` | `/bin/echo` | Command to run |
| `--arguments` | `Hello from AmSC!` | Command args |
| `--nodes` | 1 | Node count |
| `--duration` | 300 | Wall time (seconds) |
| `--monitor-timeout` | 600 | Seconds to wait for completion; 0 = don't monitor |
| `--explore-only` | — | List resources, skip submission |
| `--read-output PATH` | — | Read output file from a previous run |

## Supported Facilities

| Facility | Compute Resource | Filesystem Resource |
|----------|-----------------|---------------------|
| ALCF | Polaris | Home |
| NERSC | compute | homes |

Both facilities are built into the SDK (v0.4.2+). The API is identical across facilities — only config values (resource names, paths, queues) differ.

## Troubleshooting

### Persistent 401 errors after authenticating

If you complete the Globus login but still get `AuthenticationError: Authentication failed (401)`, your browser may be reusing a cached Globus session with a different identity. To fix:

1. Clear your browser cookies for `globus.org` (where the auth code is provided)
2. Re-run the script — it will prompt a fresh login
