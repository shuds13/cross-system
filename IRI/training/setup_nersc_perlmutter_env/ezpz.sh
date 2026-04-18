#!/bin/bash
# Run on a Perlmutter login node to pre-stage the ezpz venv.
# The venv is stored at $SCRATCH/amsc-envs/ezpz and accessible from compute nodes.
#
# Module versions may need updating — check: module avail cudatoolkit pytorch

set -e

if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

module load cudatoolkit/12.9 nccl/2.24.3 pytorch cray-mpich

VENV_DIR="${SCRATCH}/amsc-envs/ezpz"
mkdir -p "$(dirname "${VENV_DIR}")"

uv venv --python="$(which python3)" --system-site-packages "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"
uv pip install --no-cache "git+https://github.com/saforem2/ezpz[mpi]"

echo "Done. Venv at: ${VENV_DIR}"
echo "Add to envs.yaml:"
echo "  nersc:"
echo "    ezpz:"
echo "      venv: ${VENV_DIR}"
