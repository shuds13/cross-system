import json
import os
import yaml
from globus_compute_sdk import Executor

ENDPOINT_ID = os.environ["GLOBUS_COMPUTE_ENDPOINT_ID"]
NUM_TASKS = 8  # 2 nodes * 4 A100 GPUs

with open("run_config.yaml") as f:
    USER_RUN_CONFIG = yaml.safe_load(f)


def gpu_multiply(task_id, n=1000000):
    """Multiply two tensors on a Polaris A100 GPU."""
    import os
    import socket
    import torch

    device = "cuda"

    a = torch.arange(1, n + 1, device=device)
    b = torch.full((n,), float(task_id), device=device)
    c = a * b

    return {
        "task_id": task_id,
        "hostname": socket.gethostname(),
        "GPU": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "first": float(c[0].cpu()),
        "last": float(c[-1].cpu()),
    }


with Executor(
    endpoint_id=ENDPOINT_ID,
    user_endpoint_config=USER_RUN_CONFIG,
) as ex:
    futs = [ex.submit(gpu_multiply, task_id) for task_id in range(NUM_TASKS)]
    results = [f.result() for f in futs]
    for r in results:
        print(r)

with open("results.json", "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
