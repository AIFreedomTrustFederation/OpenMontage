"""The federation's verify command must execute tests, not just inspect Git."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess


ROOT = Path(__file__).resolve().parents[2]


def _verify_argv() -> list[str]:
    manifest = json.loads((ROOT / "aift.repo.json").read_text(encoding="utf-8"))
    argv = shlex.split(manifest["commands"]["verify"])
    assert argv == ["make", "test-contracts"], (
        "Federation verification must run the repository's contract-test target"
    )
    return argv


def test_federation_verify_targets_contract_suite() -> None:
    _verify_argv()
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "test-contracts:\n\t$(PYTHON) -m pytest tests/contracts/ -v\n" in makefile


def test_federation_verify_propagates_failure(tmp_path: Path) -> None:
    argv = _verify_argv()
    (tmp_path / "Makefile").write_text("test-contracts:\n\t@exit 19\n", encoding="utf-8")
    result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode != 0, "A failed test suite must fail federation verification"


def test_federation_verify_accepts_success(tmp_path: Path) -> None:
    argv = _verify_argv()
    (tmp_path / "Makefile").write_text("test-contracts:\n\t@echo contract-ok\n", encoding="utf-8")
    result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "contract-ok" in result.stdout


def test_federation_documentation_matches_manifest() -> None:
    _verify_argv()
    doc = (ROOT / "FEDERATION.md").read_text(encoding="utf-8")
    assert "Verify (requires Python test dependencies and Make, from the repository root):\n\n```bash\nmake test-contracts\n```" in doc
    assert "does not validate end-to-end rendering" in doc
