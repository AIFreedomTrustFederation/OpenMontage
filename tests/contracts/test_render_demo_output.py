"""The documented zero-key demo command must fail without a usable MP4."""

from pathlib import Path
import json
import shutil
import subprocess

import pytest

import render_demo


@pytest.fixture
def props(tmp_path: Path) -> Path:
    path = tmp_path / "demo.json"
    path.write_text('{"cuts": [{"type": "title"}]}', encoding="utf-8")
    return path


def _stub_renderer(
    monkeypatch: pytest.MonkeyPatch,
    output_bytes: bytes | None,
    *,
    probe_exit: int = 0,
    probe_result: str | None = None,
) -> None:
    valid_probe = {
        "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
        "format": {"duration": "2.0"},
    }

    def fake_run(args, *, cwd=None, check=True, capture_output=False, text=False):
        if args[1:4] == ["remotion", "render", "src/index.tsx"]:
            assert args[4] == "Explainer"
            assert cwd == render_demo.COMPOSER_DIR
            assert check is True
            if output_bytes is not None:
                Path(args[5]).write_bytes(output_bytes)
            return subprocess.CompletedProcess(args, 0)

        assert args[0] == "ffprobe"
        assert check is True and capture_output is True and text is True
        if probe_exit:
            raise subprocess.CalledProcessError(probe_exit, args)
        return subprocess.CompletedProcess(
            args, 0, stdout=probe_result if probe_result is not None else json.dumps(valid_probe)
        )

    monkeypatch.setattr(render_demo.subprocess, "run", fake_run)
    monkeypatch.setattr(render_demo, "find_command", lambda *names: "ffprobe")

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


def test_corrupt_nonempty_mp4_is_rejected(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-empty file is not necessarily a decodable video."""
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(monkeypatch, b"not an MP4 container", probe_exit=1)
    with pytest.raises(RuntimeError, match="ffprobe|decodable|video"):
        render_demo.render_demo("corrupt", props, "npx")
    assert not (tmp_path / "renders" / "corrupt.mp4").exists()


def test_probe_without_video_stream_is_rejected(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(
        monkeypatch,
        b"container bytes",
        probe_result=json.dumps({"streams": [{"codec_type": "audio"}], "format": {"duration": "2.0"}}),
    )
    with pytest.raises(RuntimeError, match="ffprobe validation"):
        render_demo.render_demo("no-video", props, "npx")
    assert not (tmp_path / "renders" / "no-video.mp4").exists()


def test_zero_duration_is_rejected_and_existing_render_is_preserved(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "renders"
    output_dir.mkdir()
    existing = output_dir / "old.mp4"
    existing.write_bytes(b"previous verified video")
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", output_dir)
    _stub_renderer(
        monkeypatch,
        b"container bytes",
        probe_result=json.dumps({
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
            "format": {"duration": "0"},
        }),
    )
    with pytest.raises(RuntimeError, match="ffprobe validation"):
        render_demo.render_demo("old", props, "npx")
    assert existing.read_bytes() == b"previous verified video"
    assert not list(output_dir.glob(".*.mp4"))


def test_missing_ffprobe_fails_closed(
    tmp_path: Path, props: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(render_demo, "OUTPUT_DIR", tmp_path / "renders")
    _stub_renderer(monkeypatch, b"container bytes")
    monkeypatch.setattr(render_demo, "find_command", lambda *names: None)
    with pytest.raises(RuntimeError, match="ffprobe.*required"):
        render_demo.render_demo("no-probe", props, "npx")
    assert not (tmp_path / "renders" / "no-probe.mp4").exists()


def test_real_ffprobe_accepts_video_and_rejects_invalid_bytes(tmp_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        pytest.skip("FFmpeg/ffprobe not available on this runner")

    valid = tmp_path / "valid.mp4"
    subprocess.run(
        [
            ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "lavfi",
            "-i", "color=c=black:s=16x16:r=5:d=1",
            "-c:v", "mpeg4", "-y", str(valid),
        ],
        check=True,
    )
    render_demo.validate_rendered_mp4(valid)

    invalid = tmp_path / "invalid.mp4"
    invalid.write_bytes(b"not an MP4")
    with pytest.raises(RuntimeError, match="ffprobe validation"):
        render_demo.validate_rendered_mp4(invalid)
