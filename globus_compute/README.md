# Globus Compute — Cross-System GPU Examples

User-managed endpoint examples for running GPU tasks on DOE HPC systems via
Globus Compute.

## Accelerator Pinning (GlobusComputeEngine)

These examples use `GlobusComputeEngine` with `available_accelerators` in the
endpoint config template. This gives each worker exclusive access to a specific
GPU — the endpoint handles device assignment automatically.

This is different from the **simple launcher** approach (used by e.g. the ALCF
multi-user endpoint as of April 2026), where all GPUs are visible to every worker and tasks must
manually set `CUDA_VISIBLE_DEVICES` or equivalent to avoid contention.

With accelerator pinning, submitted functions don't need any device management
code — they just run on whichever GPU the endpoint assigned.

## Test Problem

Each task multiplies two PyTorch tensors on a GPU:

```
a = [1, 2, 3, ..., n]     b = [task_id, task_id, ..., task_id]

c = a * b  →  [task_id, 2*task_id, 3*task_id, ..., n*task_id]
```

Returns the first and last elements to verify correctness.

## Systems

| System | GPUs/node | Accelerator type | Scheduler |
|--------|-----------|------------------|-----------|
| [Polaris](polaris/) | 4 (NVIDIA A100) | CUDA | PBS |
| [Aurora](aurora/) | 12 (Intel GPU tiles) | Intel XPU | PBS |

## See also

- [troubleshooting.md](troubleshooting.md) — common issues and log locations
