# SPDX-License-Identifier: GPL-3.0-or-later
"""composer.json matches Ouralia's dcs_composer.c as it is now (decision 12: Maestro follows a moving composer)."""
import os, subprocess, sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OURALIA = os.environ.get("MAESTRO_OURALIA", os.path.join(os.path.dirname(ROOT), "Ouralia"))


@pytest.mark.skipif(not os.path.exists(os.path.join(OURALIA, "dcs", "src", "dcs_composer.c")), reason="no Ouralia")
def test_in_step_with_ouralia():
    p = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_check.py")], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
