# Globus Compute on Aurora

Sends a batch of calculations that run on one GPU tile each. By default, uses one node
on Aurora. Run configuration can be modified in run_config.yaml.

## On Aurora

The file `globus_config_file/user_config_template.yaml.j2` must be copied to Aurora.
Instructions below will show when to put in place.

```bash
module load frameworks
python -m venv ~/venvs/gcompute --system-site-packages
source ~/venvs/gcompute/bin/activate
pip install globus-compute-endpoint globus-compute-sdk
```

To create an endpoint

```bash
globus-compute-endpoint configure aurora_test
```

Put your endpoint config here:

```bash
cp user_config_template.yaml.j2 ~/.globus_compute/aurora_test/
```

Start endpoint and copy the endpoint ID provided

```bash
globus-compute-endpoint start aurora_test
```

You may need to authenticate on Globas (via a link if given).


## Laptop / front-end

Check:
- Ensure Python version matches that on Aurora.
- Your Aurora project (account) is set in `run_config.yaml'

Set the environment variable used in the Python script and run.

```bash
pip install globus-compute-sdk pyyaml
export GLOBUS_COMPUTE_ENDPOINT_ID=<your-endpoint-id>
python run_aurora.py
```

## Checking

On Aurora, start a new terminal.

To see jobs added to queue.

```bash
qstat -fu $USER
```

should show a job queuing or running.

To list endpoints
```bash
globus-compute-endpoint list
```
