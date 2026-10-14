"""The documented HyperFrames doctor command must reflect probe failures in its exit code."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU make unavailable")
@pytest.mark.parametrize("success", [True, False])
def test_hyperframes_doctor_propagates_probe_status(tmp_path: Path, success: bool) -> None:
    # Isolate the probe so CI needs neither network access nor Node/FFmpeg.
    package = tmp_path / "tools" / "video"
    package.mkdir(parents=True)
    (package / "hyperframes_compose.py").write_text(
        "from types import SimpleNamespace\n"
        "class HyperFramesCompose:\n"
        "    def execute(self, inputs):\n"
        "        assert inputs == {'operation': 'doctor'}\n"
        f"        return SimpleNamespace(success={success!r}, "
        "data={'probe': 'synthetic'}, error='simulated unavailable')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        ["make", "--no-print-directory", "-f", str(ROOT / "Makefile"),
         "hyperframes-doctor", f"PYTHON={sys.executable}"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert (result.returncode == 0) is success, result.stdout + result.stderr
    assert ("OK" if success else "FAIL: simulated unavailable") in result.stdout
