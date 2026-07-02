#!/usr/bin/env bash
# Build a cyclonedds==0.10.5 manylinux wheel for a given Python version and
# copy it into this directory.
#
# Usage:
#   ./build_cyclonedds_wheel.sh <python-tag> [output-dir]
#
# Arguments:
#   python-tag  : py311 or py312
#   output-dir  : destination for the wheel (default: this directory)
#
# Examples:
#   ./build_cyclonedds_wheel.sh py311
#   ./build_cyclonedds_wheel.sh py312 /tmp/out

set -euo pipefail

# Pinned cibuildwheel version and manylinux image digest for bit-for-bit
# reproducible builds. Update both together when intentionally upgrading.
CIBUILDWHEEL_VERSION="3.4.1"
MANYLINUX_IMAGE="quay.io/pypa/manylinux_2_28_x86_64@sha256:853663dc8253b62be437bb52a5caecffd020792af4442f55d927d22e0ea795ae"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
    echo "Usage: $0 <python-tag> [output-dir]  (e.g. py311 or py312)" >&2
    exit 1
fi

PYTHON_TAG="$1"
OUTPUT_DIR="${2:-$SCRIPT_DIR}"
# Convert "py311" -> "cp311"
CP_TAG="cp${PYTHON_TAG#py}"
BUILD_ID="${CP_TAG}-manylinux_x86_64"

# Fix the umask so git creates files with deterministic permissions (0644/0755)
# regardless of the caller's umask. Without this, Bazel's test runner uses a
# different umask than a regular shell, causing pip to record different Unix
# permission bits in the wheel ZIP and producing a different archive SHA.
umask 0022

cd "${REPO_ROOT}"

# Freeze build timestamps to the source commit time for deterministic output.
SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
export SOURCE_DATE_EPOCH

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "==> Setting up venv and installing cibuildwheel ${CIBUILDWHEEL_VERSION} ..."
python3 -m venv "${WORK_DIR}/.venv"
"${WORK_DIR}/.venv/bin/pip3" install --quiet "cibuildwheel==${CIBUILDWHEEL_VERSION}"

echo "==> Building wheel for ${PYTHON_TAG} (${BUILD_ID}) ..."
# These variables pin the build environment (container image, dependency
# versions, timestamps) to produce a bit-for-bit reproducible wheel SHA.
# Changing or removing any of them will change the output wheel and require
# rebuilding and recommitting the wheels in this directory.
CIBW_MANYLINUX_X86_64_IMAGE="${MANYLINUX_IMAGE}" \
CIBW_ENVIRONMENT_PASS="SOURCE_DATE_EPOCH" \
CIBW_TEST_COMMAND="" \
CIBW_DEPENDENCY_VERSIONS="pinned" \
"${WORK_DIR}/.venv/bin/cibuildwheel" --output-dir "${WORK_DIR}/wheelhouse" --only "${BUILD_ID}"

WHEEL="$(ls "${WORK_DIR}/wheelhouse"/*.whl)"
WHEEL_BASENAME="$(basename "$WHEEL")"

echo "==> Copying ${WHEEL_BASENAME} -> ${OUTPUT_DIR}/"
cp "$WHEEL" "${OUTPUT_DIR}/"
echo "==> Done: ${OUTPUT_DIR}/${WHEEL_BASENAME}"
