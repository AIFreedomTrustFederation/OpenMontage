"""A successful demo render must produce a new nonempty video, not stale output."""

from pathlib import Path
import subprocess

import pytest

import render_demo


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    output_dir = tmp_path / "renders"
    props_path = tmp_path / "demo.json"
    props_path.write_text('{"cuts": [{"type": "text_card"}]}', encoding="utf-8")
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", output_dir)
    return output_dir, props_path


def test_missing_output_must_fail(fixture, monkeypatch):
    output_dir, props = fixture
    monkeypatch.setattr(render_demo.subprocess, "run", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="nonempty"):
        render_demo.render_demo("sample", props, "npx")
    assert not (output_dir / "sample.mp4").exists()


def test_empty_output_must_fail(fixture, monkeypatch):
    output_dir, props = fixture

    def fake_render(args, **kwargs):
        Path(args[5]).touch()

    monkeypatch.setattr(render_demo.subprocess, "run", fake_render)
    with pytest.raises(RuntimeError, match="nonempty"):
        render_demo.render_demo("sample", props, "npx")
    assert not (output_dir / "sample.mp4").exists()


def test_successful_render_publishes_new_video(fixture, monkeypatch):
    output_dir, props = fixture
    output_dir.mkdir()
    (output_dir / "sample.mp4").write_bytes(b"OLD")

    def fake_render(args, **kwargs):
        assert args[:5] == ["npx", "remotion", "render", "src/index.tsx", "Explainer"]
        assert kwargs["check"] is True
        Path(args[5]).write_bytes(b"NEW VIDEO")

    monkeypatch.setattr(render_demo.subprocess, "run", fake_render)
    render_demo.render_demo("sample", props, "npx")
    assert (output_dir / "sample.mp4").read_bytes() == b"NEW VIDEO"


def test_missing_new_render_must_not_reuse_old_video(fixture, monkeypatch):
    output_dir, props = fixture
    output_dir.mkdir()
    (output_dir / "sample.mp4").write_bytes(b"OLD")
    monkeypatch.setattr(render_demo.subprocess, "run", lambda *a, **k: None)
    with pytest.raises(RuntimeError, match="nonempty"):
        render_demo.render_demo("sample", props, "npx")
    assert (output_dir / "sample.mp4").read_bytes() == b"OLD"


def test_failed_renderer_preserves_existing_video(fixture, monkeypatch):
    output_dir, props = fixture
    output_dir.mkdir()
    (output_dir / "sample.mp4").write_bytes(b"OLD")

    def fake_render(args, **kwargs):
        Path(args[5]).write_bytes(b"PARTIAL")
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(render_demo.subprocess, "run", fake_render)
    with pytest.raises(subprocess.CalledProcessError):
        render_demo.render_demo("sample", props, "npx")
    assert (output_dir / "sample.mp4").read_bytes() == b"OLD"


def test_cli_reports_failure_when_renderer_writes_no_output(tmp_path):
    """Exercise the actual script exit code with a zero-exit fake npx binary."""
    import os
    import shutil
    import sys

    script = tmp_path / "render_demo.py"
    shutil.copyfile(render_demo.__file__, script)
    composer = tmp_path / "remotion-composer"
    props_dir = composer / "public" / "demo-props"
    props_dir.mkdir(parents=True)
    (composer / "node_modules").mkdir()
    (props_dir / "sample.json").write_text('{"cuts": [{}]}', encoding="utf-8")
    output = tmp_path / "projects" / "demos" / "renders" / "sample.mp4"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"PREVIOUS GOOD RENDER")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_npx = fake_bin / "npx"
    fake_npx.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_npx.chmod(0o755)
    env = dict(os.environ, PATH=f"{fake_bin}{os.pathsep}{os.environ['PATH']}", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-B", str(script), "sample"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode != 0, result.stdout
    assert "nonempty MP4" in result.stderr
    assert output.read_bytes() == b"PREVIOUS GOOD RENDER"
