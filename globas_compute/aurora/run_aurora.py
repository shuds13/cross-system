import os
import yaml
from globus_compute_sdk import Executor

ENDPOINT_ID = os.environ["GLOBUS_COMPUTE_ENDPOINT_ID"]
NUM_TASKS = 12

with open("run_config.yaml") as f:
    USER_RUN_CONFIG = yaml.safe_load(f)

def gpu_multiply_check(task_id, n=1000):
    import torch

    device = "xpu"
    if not torch.xpu.is_available():
        raise RuntimeError(f"{device} not available")

    a = torch.arange(1, n + 1, device=device)
    b = torch.full((n,), float(task_id), device=device)
    c = a * b

    return {
        "task_id": task_id,
        "device": str(c.device),
        "first": float(c[0].cpu()),
        "last": float(c[-1].cpu()),
    }

with Executor(
    endpoint_id=ENDPOINT_ID,
    user_endpoint_config=USER_RUN_CONFIG,
) as ex:
    futs = [ex.submit(gpu_multiply_check, task_id) for task_id in range(1, NUM_TASKS + 1)]
    results = [f.result() for f in futs]
    print(results)
