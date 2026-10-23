# SPDX-License-Identifier: GPL-3.0-or-later
"""maestro.port sends exactly what Ouralia's dcs_composer sends (runner.py), scenario by scenario."""
import json, os, subprocess, sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import runner   # noqa: E402

missing = [p for p in (runner.LIB, runner.DCS_LIB, runner.DCS_SRC) if not os.path.exists(p)]
stale = not missing and os.path.getmtime(runner.DCS_LIB) < os.path.getmtime(runner.DCS_SRC)
pytestmark = pytest.mark.skipif(bool(missing) or stale, reason=(
    f"Ouralia's test build is missing ({missing})" if missing else
    "Ouralia's dcs lib is older than dcs_composer.c: run `make -C dcs` in Ouralia") + " (MAESTRO_OURALIA sets where)")


@pytest.mark.parametrize("name", sorted(runner.scenarios()))
def test_parity(name, tmp_path):
    out = tmp_path / "result.json"
    p = subprocess.run([sys.executable, os.path.join(HERE, "runner.py"), name, str(out)],
                       capture_output=True, text=True, timeout=600)
    assert p.returncode == 0, p.stderr[-2000:]
    r = json.loads(out.read_text())
    assert r["ok"], f"{name}: differs at step {r['step']} {r['message']}: C {r['c']} / port {r['port']}"
    assert r["outputs"] > 50, f"{name}: only {r['outputs']} outputs, the scenario measures little"
