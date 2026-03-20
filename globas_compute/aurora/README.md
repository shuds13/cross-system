# Globus Compute on Aurora

Sends a batch of calculations that run on one GPU tile each. By default, uses two nodes
on Aurora.

The Run configuration can be modified user side in `run_config.yaml`. You must set
"account" to your Aurora project in this file.

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

You may need to authenticate on Globus (via a link if given).


## Laptop / front-end

Check:
- Ensure Python version matches that on Aurora.
- Your Aurora project (account) is set in `run_config.yaml`

Set the environment variable used in the Python script and run.

```bash
pip install globus-compute-sdk pyyaml
export GLOBUS_COMPUTE_ENDPOINT_ID=<your-endpoint-id>
python run_aurora.py
```

This may take a while as the job will have to queue on Aurora before running.

To use more nodes, increase `num_nodes` in `run_config.yaml`, and
make sure `NUM_TASKS` in `run_aurora.py` is enough to use all nodes.


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

## Example Output on 2 nodes (24 tasks)

Tasks 1–12 ran on `x4707c0s6b0n0`
Tasks 13–24 ran on `x4707c0s7b0n0`

```bash
python run_aurora.py
{'task_id': 1, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '1', 'first': 1.0, 'last': 1000000.0}
{'task_id': 2, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '0', 'first': 2.0, 'last': 2000000.0}
{'task_id': 3, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '2', 'first': 3.0, 'last': 3000000.0}
{'task_id': 4, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '4', 'first': 4.0, 'last': 4000000.0}
{'task_id': 5, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '6', 'first': 5.0, 'last': 5000000.0}
{'task_id': 6, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '3', 'first': 6.0, 'last': 6000000.0}
{'task_id': 7, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '7', 'first': 7.0, 'last': 7000000.0}
{'task_id': 8, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '5', 'first': 8.0, 'last': 8000000.0}
{'task_id': 9, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '8', 'first': 9.0, 'last': 9000000.0}
{'task_id': 10, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '10', 'first': 10.0, 'last': 10000000.0}
{'task_id': 11, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '9', 'first': 11.0, 'last': 11000000.0}
{'task_id': 12, 'hostname': 'x4707c0s6b0n0', 'GPU tile': '11', 'first': 12.0, 'last': 12000000.0}
{'task_id': 13, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '1', 'first': 13.0, 'last': 13000000.0}
{'task_id': 14, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '0', 'first': 14.0, 'last': 14000000.0}
{'task_id': 15, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '3', 'first': 15.0, 'last': 15000000.0}
{'task_id': 16, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '4', 'first': 16.0, 'last': 16000000.0}
{'task_id': 17, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '9', 'first': 17.0, 'last': 17000000.0}
{'task_id': 18, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '5', 'first': 18.0, 'last': 18000000.0}
{'task_id': 19, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '11', 'first': 19.0, 'last': 19000000.0}
{'task_id': 20, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '2', 'first': 20.0, 'last': 20000000.0}
{'task_id': 21, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '6', 'first': 21.0, 'last': 21000000.0}
{'task_id': 22, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '7', 'first': 22.0, 'last': 22000000.0}
{'task_id': 23, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '10', 'first': 23.0, 'last': 23000000.0}
{'task_id': 24, 'hostname': 'x4707c0s7b0n0', 'GPU tile': '8', 'first': 24.0, 'last': 24000000.0}
```
