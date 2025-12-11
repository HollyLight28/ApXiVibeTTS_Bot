from pathlib import Path

import pytest

from app.audio_utils import merge_wavs_to_mp3_ffmpeg


def test_merge_wavs_to_mp3_creates_list_and_calls_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    temp_dir = tmp_path / "temp_audio"
    temp_dir.mkdir()

    wav1 = temp_dir / "chunk_1.wav"
    wav2 = temp_dir / "chunk_2.wav"
    wav1.write_bytes(b"\x00\x00")
    wav2.write_bytes(b"\x00\x00")

    out_dir = tmp_path / "out"
    out_mp3 = out_dir / "tts_test.mp3"

    calls = []

    def fake_run(cmd: list[str], check: bool = True) -> None:  # noqa: ARG001
        calls.append(cmd)

    monkeypatch.setattr("app.audio_utils.subprocess.run", fake_run)

    merge_wavs_to_mp3_ffmpeg([wav1, wav2], out_mp3, title="Hello", artist="ApXiVibeTTS")

    list_file = out_dir / "concat_list.txt"
    assert list_file.exists()
    content = list_file.read_text(encoding="utf-8").strip().splitlines()
    assert content[0].startswith("file ") and str(wav1.resolve()).replace("\\", "/") in content[0]
    assert content[1].startswith("file ") and str(wav2.resolve()).replace("\\", "/") in content[1]

    # Ensure ffmpeg was called with the list file as absolute path
    assert calls, "ffmpeg not invoked"
    cmd = calls[0]
    assert "-i" in cmd
    list_arg = cmd[cmd.index("-i") + 1]
    assert Path(list_arg).is_absolute()


def test_merge_wavs_to_mp3_empty_list(tmp_path: Path) -> None:
    out_mp3 = tmp_path / "out" / "tts_test.mp3"
    with pytest.raises(ValueError):
        merge_wavs_to_mp3_ffmpeg([], out_mp3)
