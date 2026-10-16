"""The Makefile's HyperFrames doctor target must report failure to callers."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU Make is unavailable")
@pytest.mark.parametrize("healthy", [True, False], ids=["healthy", "unavailable"])
def test_hyperframes_doctor_propagates_status(tmp_path: Path, healthy: bool) -> None:
    # Run the real Makefile recipe against a stub ToolResult, without network,
    # credentials, npm downloads, or an installed HyperFrames runtime.
    repo_root = Path(__file__).resolve().parents[2]
    package = tmp_path / "tools" / "video"
    package.mkdir(parents=True)
    (tmp_path / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "hyperframes_compose.py").write_text(
        """import os
from types import SimpleNamespace

class HyperFramesCompose:
    def execute(self, inputs):
        assert inputs == {"operation": "doctor"}
        ok = os.environ["TEST_HF_HEALTHY"] == "1"
        return SimpleNamespace(success=ok, data={"runtime_available": ok},
                               error=None if ok else "synthetic unavailable")
""",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    env["TEST_HF_HEALTHY"] = "1" if healthy else "0"
    proc = subprocess.run(
        ["make", "-f", str(repo_root / "Makefile"), "hyperframes-doctor", f"PYTHON={sys.executable}"],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if healthy:
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "OK" in proc.stdout
    else:
        assert proc.returncode != 0, proc.stdout + proc.stderr
        assert "FAIL: synthetic unavailable" in proc.stdout
