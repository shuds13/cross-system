#!/bin/bash
# Run on a Polaris login node to pre-stage the ezpz venv.
# The venv is stored at $HOME/amsc-envs/ezpz and accessible from compute nodes.

set -e

export http_proxy="http://proxy.alcf.anl.gov:3128"
export https_proxy="http://proxy.alcf.anl.gov:3128"
export HTTP_PROXY="http://proxy.alcf.anl.gov:3128"
export HTTPS_PROXY="http://proxy.alcf.anl.gov:3128"
export ftp_proxy="http://proxy.alcf.anl.gov:3128"

module use /soft/modulefiles
module load conda
conda activate

VENV_DIR="${HOME}/amsc-envs/ezpz"
mkdir -p "$(dirname "${VENV_DIR}")"

python -m venv --system-site-packages "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
pip install --no-cache-dir "git+https://github.com/saforem2/ezpz"
pip install --no-cache-dir mpi4py

echo "Done. Venv at: ${VENV_DIR}"
