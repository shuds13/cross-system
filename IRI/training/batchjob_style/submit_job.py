#!/usr/bin/env python3
import datetime, pathlib
from amsc_client import Client
from iri_api_autogen.models import JobAttributes, JobSpec, ResourceSpec
from iri_utils import facilities, get_home_dir, get_custom_attrs, build_job_cmd, upload_files, monitor_and_read

user_config = {
    "alcf": {
        "account":  "datascience",
        "username": "shudson",
        "queue":    "debug",
    },
    "nersc": {
        "account":  "amsc013",
        "username": "shuds",
        "queue":    "express_amsc",
    },
}

# -----------------------------------------------------------------------

FACILITY = "nersc"
ACCOUNT  = user_config[FACILITY]["account"]
USERNAME = user_config[FACILITY]["username"]
QUEUE    = user_config[FACILITY]["queue"]
JOB_NAME  = "ezpz-test"
NODES     = 1
GPUS_PER_NODE = 4
DURATION  = 600   # seconds
MONITOR_TIMEOUT = DURATION+60  # 0 to not monitor.

ENV_NAME  = "ezpz"  # To load environment from catalog.
RUN       = "ezpz launch python3 -m ezpz.examples.test"
ARGUMENTS = ""

CATALOG_PATH = pathlib.Path(__file__).parent.parent / "envs.yaml"
UPLOAD_FILES = []  # list of (local_path, remote_path) if files need sending
# -----------------------------------------------------------------------

client = Client(token="not-needed-for-facilities")
facility = client.facility(FACILITY)
config = facilities[FACILITY]
filesystem = facility.resource(config["fs_resource"])

home_dir = get_home_dir(FACILITY, USERNAME)
output_dir = f"{home_dir}/iri_job_outputs"
job_name = f"{JOB_NAME}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

if UPLOAD_FILES:
    upload_files(filesystem, UPLOAD_FILES)

cmd = build_job_cmd(CATALOG_PATH, FACILITY, ENV_NAME, RUN, ARGUMENTS)

body = JobSpec(
    executable="/bin/bash",
    arguments=["-l", "-c", cmd],
    directory=home_dir,
    name=job_name,
    stdout_path=f"{output_dir}/{job_name}.stdout",
    stderr_path=f"{output_dir}/{job_name}.stderr",
    resources=ResourceSpec(
        node_count=NODES,
        processes_per_node=GPUS_PER_NODE,
        gpu_cores_per_process=1,
    ),
    attributes=JobAttributes(
        duration=DURATION,
        queue_name=QUEUE,
        account=ACCOUNT,
        custom_attributes=get_custom_attrs(FACILITY),
    ),
)

compute = facility.resource(config["compute_resource"])
job = compute.submit(body=body)
print(f"Job {job.id} submitted (state: {job.state})")
print(f"stdout: {output_dir}/{job_name}.stdout")

monitor_and_read(job, filesystem, f"{output_dir}/{job_name}.stdout", MONITOR_TIMEOUT)
