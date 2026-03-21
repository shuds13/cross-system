# IRI Perlmutter

> **Note:** This is Work In Progress. May NOT currently work. And process likely to change.

> **Note:** Example running a Python workflow (need to add example with srun launcher).

Submit to Perlmutter via IRI interface.

These instructions use the Rest API directly.

## Authorization

First you must obtain a Auth token (currently uses SFAPI tokens).

Log in at https://iris.nersc.gov

Go to `Profile` in blue ribbon.

Scroll down to `Superfacility API Clients` and click + **New Client**

Ref: https://docs.nersc.gov/services/sfapi/authentication/

In box:
    Choose a client name, select "Create Globus Token" and move slider to Red.
    Use "IP Presets" dropdown box. Select where you will run from:
        e.g., From your own computer select "Your IP". To run from Spin, select that.
    -> OK

You will be guided through Globus auth (Download your client_id private key - including PEM version).


## Obtain token

```bash
pip install authlib
```

Run `get_sfapi_token.py` in directory with the downloaded `clientid.txt` and `priv_key.pem` files.

```bash
export IRI_TOKEN="$(python get_sfapi_token.py)"
```

## Submitting job on Perlmutter via IRI.

Set your remote directory where you will run on Perlmutter. E.g.,

```bash
export REMOTE_DIR='/global/cfs/cdirs/<project_id>/shudson/amsc_libe'
```

You will need to update `iri_req.json` to:
- Replace "<remote_dir>" with this directory.
- Replace `_amsc_env` with a `venv` virtual environment to be activated.
- Other details as required.

To get the correct resource ID for Perlmutter compute nodes:

```bash
export IRI_BASE='https://api.iri.nersc.gov/api/v1'
export RESOURCE_ID="$(curl -s -H "Authorization: Bearer $IRI_TOKEN" "$IRI_BASE/status/resources" | jq -r '.[] | select(.group=="perlmutter" and .resource_type=="compute" and .name=="compute") | .id')"
```

THIS DOES NOT WORK... JUST COPY FILES TO PERLMUTTER
If files need transferring (push user run scripts). Alternatively, have files in place.

```bash
export FS_RESOURCE_ID='59e80c79-4dfd-4c53-9c07-7405685fcd37'  # this can be obtained similar to RESOURCE_ID
export UPLOAD_URL="$IRI_BASE/filesystem/upload/$FS_RESOURCE_ID"
curl -X POST -H "Authorization: Bearer $IRI_TOKEN" -F "file=@run_libe.py" -F "path=$REMOTE_DIR/run_test/run_libe.py" "$UPLOAD_URL"
curl -X POST -H "Authorization: Bearer $IRI_TOKEN" -F "file=@simf.py" -F "path=$REMOTE_DIR/run_test/simf.py" "$UPLOAD_URL"
```

Copying files normally.

```bash
scp run_libe.py perlmutter:/$REMOTE_DIR
scp simf.py perlmutter:/$REMOTE_DIR
```

Run job.

```bash
curl -X POST -H "Authorization: Bearer $IRI_TOKEN" -H "Content-Type: application/json" "https://api.iri.nersc.gov/api/v1/compute/job/$RESOURCE_ID" -d @iri_req.json
```
