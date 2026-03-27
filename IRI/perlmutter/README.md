# IRI Perlmutter

> **Note:** This is Work In Progress.

> **Note:** Example running a Python workflow (need to add example with srun launcher).

Submit to Perlmutter via IRI interface.

These instructions use the Rest API directly.

## Pre-requisite

Requires authorization to use IRI at NERSC.

Need `token_manager.py` script.

## Authorization

First you must obtain an IRI Auth token.

On your client system (e.g., laptop):

```bash
python token_manager.py ensure --force-login --prompt-login --validate-iri
```

You may be prompted to authorize via Globus.

If successful, token is written to `$HOME/.globus/auth_tokens.json`.


```bash
export IRI_TOKEN=$(jq -r '.other_tokens[] | select(.scope|contains("iri_api")) | .access_token' "$HOME/.globus/auth_tokens.json")
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
export RESOURCE_ID=$(curl -s -H "Authorization: Bearer $IRI_TOKEN" $IRI_BASE/status/resources | jq -r '.[] | select(.group=="perlmutter" and .resource_type=="compute" and .name=="compute") | .id')
```

To submit job:

```bash
curl -X POST -H "Authorization: Bearer $IRI_TOKEN" -H "Content-Type: application/json" "$IRI_BASE/compute/job/$RESOURCE_ID" -d @iri_req.json
```
