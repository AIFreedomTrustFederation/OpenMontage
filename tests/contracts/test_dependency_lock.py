"""Contracts that keep declared dependencies aligned with the CI lock."""

from pathlib import Path
import re

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "requirements-dev.lock"
LOCKED_PACKAGE = re.compile(r"^([A-Za-z0-9_.-]+)==([^ \\]+)", re.MULTILINE)


def _declared_requirements(path: Path) -> list[Requirement]:
    declared: list[Requirement] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-r "):
            declared.extend(_declared_requirements(path.parent / line[3:].strip()))
            continue
        declared.append(Requirement(line))
    return declared


def test_dependency_lock_covers_declared_requirements_with_hashes() -> None:
    lock_text = LOCK.read_text(encoding="utf-8")
    matches = list(LOCKED_PACKAGE.finditer(lock_text))
    locked = {
        canonicalize_name(match.group(1)): match.group(2) for match in matches
    }

    for requirement in _declared_requirements(ROOT / "requirements-dev.txt"):
        name = canonicalize_name(requirement.name)
        assert name in locked, f"{requirement.name} is declared but absent from the lock"
        assert requirement.specifier.contains(
            locked[name], prereleases=True
        ), f"locked {requirement.name}=={locked[name]} violates {requirement.specifier}"

    for index, match in enumerate(matches):
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(lock_text)
        block = lock_text[match.start():block_end]
        assert "--hash=sha256:" in block, f"{match.group(1)} has no approved artifact hash"
