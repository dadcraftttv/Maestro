# S.1 optional PC runtime

DadCraft approved S.1 prep step 3 (Oct 29): install one pinned CUDA PyTorch;
no training yet. Core Maestro and its event codec never import torch.

`pyproject.toml` pins the optional `spike` extra to **torch==2.7.1+cu126**,
CUDA **12.6**. This explicit CUDA build avoids selecting a different wheel from
PyPI. The official CUDA 12.6 index supplies this Linux/Python 3.12 wheel.
Install from the Maestro directory, into its existing virtual environment:

```sh
.venv/bin/python -m pip install 'torch==2.7.1+cu126' --index-url https://download.pytorch.org/whl/cu126
```

The pin matches `[spike]`; install normal Maestro/test dependencies separately
from the usual index. No torchvision, torchaudio, model weights, system CUDA
toolkit or driver installation is required. CUDA libraries and Triton are
required transitive runtime dependencies, not additional model downloads.

PyTorch: **BSD-3-Clause**, checked before installation against the
[versioned license](https://github.com/pytorch/pytorch/blob/v2.7.1/LICENSE).
Bundled/required dependencies retain their own notices, including NVIDIA's CUDA
runtime licenses; this does not change Maestro's license. The extra is for this
PC's spike, not an Ouralia runtime dependency.

Checks: `tests/unit/test_spike_runtime.py` blocks all torch imports in a fresh
interpreter while importing `maestro` and `maestro.spike.tokens`. The CUDA test
allocates a GPU tensor, multiplies it, synchronizes, and checks exact results.
It skips if torch or CUDA is absent. Run the GPU check with device access:

```sh
.venv/bin/python -m pytest -q -n 0 tests/unit/test_spike_runtime.py
```

## Verified on this PC (Oct 29)

Installed **2.7.1+cu126**, CUDA **12.6**; RTX 2070, 8,192 MiB, driver
595.91.07, compute capability 7.5. The wheel includes `sm_75` kernels.
GPU allocation/matrix multiplication/synchronization/result checks: **2 tests
passed** (including import isolation), with device access outside the sandbox.

Download sizes from pip's rounded transfer log: torch **822.0 MB**;
new wheel downloads including required dependencies **2,991.9 MB** (~2.99 GB,
decimal); total wheel payload including cache hits **2,996.4 MB**.
These are compressed wheel sizes, not installed disk usage; small metadata
requests are excluded. Private install report/log: `private/s1_prep_step3/`.
`pip check`: no broken requirements. Before installing torch, the full suite
passed **343 tests**, with **1 CUDA skip**. With torch installed, sandboxed
CUDA still skips because the device is inaccessible there; the separate GPU
check above exercises the real device. No training or weights downloaded.
