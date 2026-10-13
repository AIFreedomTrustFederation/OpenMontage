"""Ensure the optional HyperFrames doctor target propagates probe failure."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


MAKEFILE = Path(__file__).resolve().parents[2] / "Makefile"


@pytest.mark.parametrize("healthy,expected_code", [(True, 0), (False, 2)])
def test_hyperframes_doctor_make_exit_status(tmp_path: Path, healthy: bool, expected_code: int) -> None:
    # Use an isolated module stub; no Node, FFmpeg, or network access is needed.
    module_dir = tmp_path / "tools" / "video"
    module_dir.mkdir(parents=True)
    (tmp_path / "tools" / "__init__.py").write_text("")
    (module_dir / "__init__.py").write_text("")
    (module_dir / "hyperframes_compose.py").write_text(
        "from types import SimpleNamespace\n"
        "import os\n"
        "class HyperFramesCompose:\n"
        "    def execute(self, inputs):\n"
        "        assert inputs == {'operation': 'doctor'}\n"
        "        ok = os.environ['AIFT_STUB_DOCTOR_HEALTHY'] == '1'\n"
        "        return SimpleNamespace(success=ok, data={'stub': True}, "
        "error=None if ok else 'simulated probe failure')\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    env["AIFT_STUB_DOCTOR_HEALTHY"] = "1" if healthy else "0"
    result = subprocess.run(
        ["make", "-f", str(MAKEFILE), "hyperframes-doctor", f"PYTHON={sys.executable}"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == expected_code, result.stdout + result.stderr
    assert ("OK" if healthy else "FAIL: simulated probe failure") in result.stdout
