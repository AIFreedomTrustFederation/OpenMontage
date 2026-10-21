"""The documented zero-key demo command must fail without a usable MP4."""

from pathlib import Path
import subprocess

import pytest

import render_demo


@pytest.fixture
def props(tmp_path: Path) -> Path:
    path = tmp_path / "demo.json"
    path.write_text('{"cuts": [{"type": "title"}]}', encoding="utf-8")
    return path


def _stub_renderer(monkeypatch: pytest.MonkeyPatch, output_bytes: bytes | None) -> None:
    def fake_run(args, *, cwd, check):
        assert args[1:4] == ["remotion", "render", "src/index.tsx"]
        assert args[4] == "Explainer"
        assert cwd == render_demo.COMPOSER_DIR
        assert check is True
        if output_bytes is not None:
            Path(args[5]).write_bytes(output_bytes)
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(render_demo.subprocess, "run", fake_run)


def test_missing_mp4_fails_even_if_renderer_exits_zero(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(monkeypatch, None)
    with pytest.raises(RuntimeError, match="non-empty output file"):
        render_demo.render_demo("missing", props, "npx")


def test_zero_byte_mp4_fails_even_if_renderer_exits_zero(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(monkeypatch, b"")
    with pytest.raises(RuntimeError, match="non-empty output file"):
        render_demo.render_demo("empty", props, "npx")


def test_nonempty_mp4_is_accepted(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(monkeypatch, b"fake mp4 bytes")
    render_demo.render_demo("ok", props, "npx")
    assert (tmp_path / "renders" / "ok.mp4").read_bytes() == b"fake mp4 bytes"
    assert not list((tmp_path / "renders").glob(".*.mp4"))
    assert "Done:" in capsys.readouterr().out


def test_renderer_nonzero_status_still_fails(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")

    def fake_run(args, *, cwd, check):
        raise subprocess.CalledProcessError(9, args)

    monkeypatch.setattr(render_demo.subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError) as error:
        render_demo.render_demo("failed", props, "npx")
    assert error.value.returncode == 9


def test_existing_mp4_is_not_mistaken_for_new_render(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "renders"
    output_dir.mkdir()
    existing = output_dir / "stale.mp4"
    existing.write_bytes(b"previous successful render")
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", output_dir)
    _stub_renderer(monkeypatch, None)
    with pytest.raises(RuntimeError, match="non-empty output file"):
        render_demo.render_demo("stale", props, "npx")
    assert existing.read_bytes() == b"previous successful render"
    assert not list(output_dir.glob(".*.mp4"))


def test_successful_render_atomically_replaces_previous_mp4(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "renders"
    output_dir.mkdir()
    existing = output_dir / "fresh.mp4"
    existing.write_bytes(b"previous successful render")
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", output_dir)
    _stub_renderer(monkeypatch, b"new successful render")
    render_demo.render_demo("fresh", props, "npx")
    assert existing.read_bytes() == b"new successful render"
    assert not list(output_dir.glob(".*.mp4"))
