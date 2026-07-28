## Building the wheels

Create a virtual environment, install `cibuildwheel`, and build the wheel:

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install cibuildwheel
pip install cibuildwheel

# 3. Build the wheel for a specific Python version and architecture
cibuildwheel --output-dir wheelhouse --only cp<PYVER>-manylinux_<ARCH>
```

Replace the placeholders in the `--only` selector:

- `<PYVER>` — the target CPython version: `311` (Python 3.11) or `312` (Python 3.12)
- `<ARCH>` — the target architecture: `aarch64` (ARM) or `x86_64` (Intel/AMD)

For example, to build a Python 3.12 wheel for ARM:

```bash
cibuildwheel --output-dir wheelhouse --only cp312-manylinux_aarch64
```

The built wheels are written to the `wheelhouse/` directory.

Notes:
1. `cibuildwheel` builds inside a manylinux container, so a container runtime
   (Docker or podman) must be installed and running.
2. The build configuration lives in the `[tool.cibuildwheel]` section of the
   repository's `pyproject.toml`.
3. The pinned version (0.10.5) refers to the underlying C `cyclonedds`
   library, and matches the cyclonedds version shipped with ROS 2 Jazzy:
   https://index.ros.org/p/cyclonedds/#jazzy
4. Wheels are sourced from a TRI fork of cyclonedds-python. The fork uses a
   fourth version segment (e.g. 0.10.5.1) to distinguish TRI patch releases
   from the upstream 0.10.5 release, while remaining fully compatible with it.
5. This package is a Python binding of the underlying C `cyclonedds` binary.
   `cibuildwheel` bundles the necessary shared libraries into the wheel so
   consumers do not need to install cyclonedds separately.
