"""Optional PC runtime: core imports stay independent of PyTorch."""
import subprocess
import sys

import pytest


def test_core_imports_without_torch():
    # Fresh interpreter, even when other tests have already imported torch.
    subprocess.run([sys.executable, "-c", """
import importlib.abc
import sys
class NoTorch(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'torch' or fullname.startswith('torch.'):
            raise AssertionError('core imports must not load torch')
sys.meta_path.insert(0, NoTorch())
import maestro
import maestro.spike.tokens
import maestro.spike.ngram
import maestro.spike.harness
assert not any(n == 'torch' or n.startswith('torch.') for n in sys.modules)
"""], check=True)


def test_cuda_tensor():
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available():
        pytest.skip("optional CUDA device unavailable")
    x = torch.arange(6, dtype=torch.float32, device="cuda").reshape(2, 3)
    result = x @ x.T
    torch.cuda.synchronize()
    assert result.is_cuda
    assert result.cpu().tolist() == [[5.0, 14.0], [14.0, 50.0]]
