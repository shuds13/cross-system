# Globus Compute on Polaris

Sends a batch of calculations that run on one A100 GPU each. By default, uses one node
on Polaris (4 GPUs).

The run configuration can be modified user side in `run_config.yaml`. You must set
"account" to your ALCF project in this file.

## On Polaris

The file `globus_config_file/user_config_template.yaml.j2` must be copied to Polaris.
Instructions below will show when to put in place.

```bash
module use /soft/modulefiles && module load conda && conda activate
python -m venv ~/venvs/gcompute --system-site-packages
source ~/venvs/gcompute/bin/activate
pip install globus-compute-endpoint
```

To create an endpoint

```bash
globus-compute-endpoint configure polaris
```

Put your endpoint config here:

```bash
cp user_config_template.yaml.j2 ~/.globus_compute/polaris/
```

Start endpoint and copy the endpoint ID provided

```bash
globus-compute-endpoint start polaris
```

You may need to authenticate on Globus (via a link if given).


## Laptop / front-end

Check:
- Ensure Python version matches that on Polaris (3.12).
- Your ALCF project (account) is set in `run_config.yaml`

Set the environment variable used in the Python script and run.

```bash
pip install globus-compute-sdk pyyaml
export GLOBUS_COMPUTE_ENDPOINT_ID=<your-endpoint-id>
python run_polaris.py
```

This may take a while as the job will have to queue on Polaris before running.

To use more nodes, increase `num_nodes` in `run_config.yaml`, and
make sure `NUM_TASKS` in `run_polaris.py` is enough to use all nodes.


## Checking

On Polaris, start a new terminal.

To see jobs added to queue.

```bash
qstat -fu $USER
```

should show a job queuing or running.

To list endpoints
```bash
globus-compute-endpoint list
```
