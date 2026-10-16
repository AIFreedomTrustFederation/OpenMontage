"""The HyperFrames doctor Make target must fail when its probe fails.

Use an isolated import stub to avoid network access and the optional Node/FFmpeg
runtime. The real Make recipe is exercised, not a rewritten Python equivalent.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("probe_success", "expected_message"),
    [(True, "OK"), (False, "FAIL: simulated probe failure")],
)
def test_hyperframes_doctor_propagates_probe_status(
    tmp_path: Path,
    probe_success: bool,
    expected_message: str,
) -> None:
    """A failed ToolResult must not be mistaken for a successful Make target."""
    stub_package = tmp_path / "tools" / "video"
    stub_package.mkdir(parents=True)
    (tmp_path / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (stub_package / "__init__.py").write_text("", encoding="utf-8")
    (stub_package / "hyperframes_compose.py").write_text(
        textwrap.dedent(
            f"""\
            from types import SimpleNamespace

            class HyperFramesCompose:
                def execute(self, inputs):
                    assert inputs == {{"operation": "doctor"}}
                    return SimpleNamespace(
                        success={probe_success!r},
                        data={{"stub_probe": True}},
                        error={None if probe_success else 'simulated probe failure'!r},
                    )
            """
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path)
    result = subprocess.run(
        [
            "make",
            "--no-print-directory",
            "-f",
            str(ROOT / "Makefile"),
            f"PYTHON={sys.executable}",
            "hyperframes-doctor",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert (result.returncode == 0) is probe_success, (
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert expected_message in result.stdout
    assert '"stub_probe": true' in result.stdout
