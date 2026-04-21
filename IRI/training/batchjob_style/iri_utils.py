"""Shared utilities for IRI job submission scripts."""

import pathlib
import re

import yaml
from amsc_client import ApiError
from iri_api_autogen.models import JobAttributesCustomAttributes
from iri_api_autogen.types import UNSET

ANSI = re.compile(r'\x1b\[[0-9;]*m')


facilities = {
    "alcf": {
        "compute_resource": "Polaris",
        "fs_resource": "Home",
        "home_dir": "/home/{username}",
        "custom_attributes": {"filesystems": "home:eagle"},
    },
    "nersc": {
        "compute_resource": "compute",
        "fs_resource": "homes",
        "home_dir": "/global/homes/{first}/{username}",
        "custom_attributes": {},
    },
}


def get_home_dir(facility_name, username):
    return facilities[facility_name]["home_dir"].format(username=username, first=username[0])



def get_custom_attrs(facility_name):
    config = facilities[facility_name]
    if not config.get("custom_attributes"):
        return UNSET
    custom_attrs = JobAttributesCustomAttributes()
    for k, v in config["custom_attributes"].items():
        custom_attrs.additional_properties[k] = v
    return custom_attrs


def explore(facility):
    info = facility.info()
    print(f"\nFacility: {info.name}")
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


def load_env_config(catalog_path, facility_name, env_name):
    with open(catalog_path) as f:
        catalog = yaml.safe_load(f)
    try:
        return catalog[facility_name][env_name]
    except KeyError:
        raise SystemExit(f"No '{env_name}' env configured for '{facility_name}' in {catalog_path}")


def build_env_cmd(env_cfg):
    parts = list(env_cfg.get("setup") or [])
    parts.append(f"source {env_cfg['venv']}/bin/activate")
    return parts


def build_job_cmd(catalog_path, facility_name, env_name, run, arguments=""):
    parts = []
    if env_name:
        env_cfg = load_env_config(catalog_path, facility_name, env_name)
        parts = build_env_cmd(env_cfg)
    cmd = f"{run} {arguments}".strip()
    parts.append(cmd)
    return " && ".join(parts)


def upload_files(fs, files):
    for local_path, remote_path in files:
        print(f"Uploading {local_path} -> {remote_path} ...")
        fs.fs.upload(local_path, remote_path).wait(timeout=60)
    print("Uploads done.")


def monitor_and_read(job, fs, stdout_path, timeout):
    print(f"\nWaiting up to {timeout}s ...")
    try:
        job.wait(timeout=timeout, poll_interval=5)
        print(f"Done: state={job.state}, exit_code={job.exit_code}")
    except TimeoutError:
        print(f"Timed out — last state: {job.state}")
        return
    read_output(fs, stdout_path)


def read_output(fs, stdout_path):
    for label, path in [("stdout", stdout_path), ("stderr", stdout_path.replace(".stdout", ".stderr"))]:
        try:
            task = fs.fs.download(path)
            task.wait(timeout=60)
            print(f"\n── {label} ──\n{ANSI.sub('', task.result)}")
        except ApiError:
            try:
                task = fs.fs.head(path, lines=50)
                task.wait(timeout=60)
                print(f"\n── {label} ──\n{ANSI.sub('', task.result['output']['content'])}")
            except ApiError as e:
                print(f"Could not read {label}: {e}")
