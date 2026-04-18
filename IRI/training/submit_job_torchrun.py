#!/usr/bin/env python3
"""Cross-facility job submission via the AmSC Python Client.

Works with any IRI-compliant facility (ALCF, NERSC). The SDK provides a
uniform API — only configuration values differ between sites.

Usage:
    python submit_job.py alcf --account datascience --username shudson
    python submit_job.py nersc --account amsc013 --username shuds
    python submit_job.py alcf --explore-only

The job is monitored and output returned. Use "--monitor-timeout 0" to not monitor.

If output is not returned in monitoring time, a command to read output later will be shown. E.g.:
    python submit_job.py alcf --read-output /home/shudson/iri_job_outputs/iri-run-20260417-153000.stdout
"""

import argparse
import datetime
import pathlib
import sys
import time

import yaml
from amsc_client import Client, ApiError
from iri_api_autogen.models import JobAttributes, JobAttributesCustomAttributes, JobSpec, ResourceSpec
from iri_api_autogen.types import UNSET

FACILITIES = {
    "alcf": {
        "compute_resource": "Polaris",
        "fs_resource": "Home",
        "queue": "debug",
        "home_dir": "/home/{username}",
        "custom_attributes": {"filesystems": "home"},
    },
    "nersc": {
        "compute_resource": "compute",
        "fs_resource": "homes",
        "queue": "debug",
        "home_dir": "/global/homes/{first}/{username}",
        "custom_attributes": {},
    },
}


def _load_env_config(facility_name, env_name="torchrun"):
    catalog_path = pathlib.Path(__file__).parent / "envs.yaml"
    with open(catalog_path) as f:
        catalog = yaml.safe_load(f)
    try:
        return catalog[facility_name][env_name]
    except KeyError:
        raise SystemExit(f"No '{env_name}' env configured for '{facility_name}' in envs.yaml")


def explore(facility):
    """List resources and recent incidents (no auth required)."""
    info = facility.info()
    print(f"\nFacility: {info.name}")
    print(f"{'─' * 40}")

    resources = facility.resources()
    print(f"\nResources ({len(resources)}):")
    for r in resources:
        print(f"  {r.name:12s}  {r.resource_type:10s}  {r.status}")

    incidents = facility.incidents()
    if incidents:
        print(f"\nRecent incidents ({len(incidents)}):")
        for inc in incidents[:3]:
            print(f"  - {inc.name}")
    else:
        print("\nNo active incidents.")


def submit_job(facility, config, args):
    """Submit a job and return (job, output_dir, job_name)."""
    compute = facility.resource(config["compute_resource"])
    home_dir = config["home_dir"].format(username=args.username, first=args.username[0])
    output_dir = f"{home_dir}/iri_job_outputs"
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    job_name = f"iri-run-{run_id}"

    custom_attrs = UNSET
    if config.get("custom_attributes"):
        custom_attrs = JobAttributesCustomAttributes()
        for k, v in config["custom_attributes"].items():
            custom_attrs.additional_properties[k] = v

    env_cfg = _load_env_config(args.facility, "torchrun")
    modules = env_cfg.get("modules") or []
    venv = env_cfg["venv"]
    parts = []
    if modules:
        parts.append("module load " + " ".join(modules))
    parts.append(f"source {venv}/bin/activate")
    parts.append(f"torchrun --nproc-per-node={args.gpus_per_node} -m ezpz.examples.test")
    cmd = " && ".join(parts)

    work_dir = args.directory or f"{home_dir}/ezpz"
    body = JobSpec(
        executable="/bin/bash",
        arguments=["-l", "-c", cmd],
        directory=work_dir,
        name=job_name,
        stdout_path=f"{output_dir}/{job_name}.stdout",
        stderr_path=f"{output_dir}/{job_name}.stderr",
        resources=ResourceSpec(node_count=args.nodes, processes_per_node=args.gpus_per_node, gpu_cores_per_process=1),
        attributes=JobAttributes(
            duration=args.duration,
            queue_name=config["queue"],
            account=args.account,
            custom_attributes=custom_attrs,
        ),
    )

    print(f"\nSubmitting to {compute.name} ...")
    print(f"Job spec: {body.to_dict()}")
    job = compute.submit(body=body)
    print(f"Job {job.id} submitted (state: {job.state})")
    print(f"stdout: {output_dir}/{job_name}.stdout")
    print(f"stderr: {output_dir}/{job_name}.stderr")

    return job, output_dir, job_name


def monitor_job(job, timeout, poll_interval=5):
    """Wait for a job to complete."""
    print(f"\nWaiting up to {timeout}s ...")
    try:
        job.wait(timeout=timeout, poll_interval=poll_interval)
        print(f"Done: state={job.state}, exit_code={job.exit_code}")
        return True
    except TimeoutError:
        print(f"Timed out — last state: {job.state}")
        return False


def read_output(facility, config, path):
    """Read a file from the facility filesystem."""
    fs = facility.resource(config["fs_resource"])
    try:
        task = fs.fs.head(path, lines=50)
        task.wait(timeout=60)
        print(f"\n── {path} ──\n{task.result}")
    except ApiError as e:
        print(f"Could not read output: {e}")


def main():
    parser = argparse.ArgumentParser(description="Submit a job to an IRI facility")
    parser.add_argument("facility", choices=FACILITIES.keys())
    parser.add_argument("--account", help="Project allocation (required for submission)")
    parser.add_argument("--username", help="Facility username (required for submission)")
    parser.add_argument("--directory", help="Working directory on the remote system (default: /home/<username>/ezpz)")
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--gpus-per-node", type=int, default=4)
    parser.add_argument("--duration", type=int, default=1800, help="Wall time in seconds")
    parser.add_argument("--monitor-timeout", type=int, default=1800, help="Seconds to wait for job completion; 0 = submit and exit")
    parser.add_argument("--explore-only", action="store_true", help="List resources and exit (no auth needed)")
    parser.add_argument("--read-output", metavar="PATH", help="Read output file from a previous run")
    args = parser.parse_args()

    config = FACILITIES[args.facility]
    client = Client(token="not-needed-for-facilities")
    facility = client.facility(args.facility)

    if args.read_output:
        read_output(facility, config, args.read_output)
        return

    explore(facility)

    if args.explore_only:
        return

    if not args.account or not args.username:
        parser.error("--account and --username are required for job submission (or use --explore-only)")

    job, output_dir, job_name = submit_job(facility, config, args)

    if args.monitor_timeout == 0:
        print(f"\nTo read output later:\n  python submit_job.py {args.facility} --read-output {output_dir}/{job_name}.stdout")
        return

    if monitor_job(job, args.monitor_timeout):
        read_output(facility, config, f"{output_dir}/{job_name}.stdout")
    else:
        print(f"\nTo read output later:\n  python submit_job.py {args.facility} --read-output {output_dir}/{job_name}.stdout")


if __name__ == "__main__":
    main()
