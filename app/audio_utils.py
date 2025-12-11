from __future__ import annotations

import subprocess
import wave
from pathlib import Path


def write_wave_from_pcm(
    file_path: Path,
    pcm: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2,
) -> None:
    # Запис PCM у WAV файл для подальшої обробки через pydub/ffmpeg
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def merge_wavs_to_mp3_ffmpeg(wavs: list[Path], out_mp3: Path, title: str | None = None, artist: str | None = None) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    if not wavs:
        raise ValueError("Список WAV порожній")
    # Створюємо тимчасовий файл-список для concat demuxer
    list_file = out_mp3.parent / "concat_list.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for p in wavs:
            f.write(f"file '{p.resolve().as_posix()}'\n")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file.resolve()),
    ]
    if title:
        cmd += ["-metadata", f"title={title}"]
    if artist:
        cmd += ["-metadata", f"artist={artist}"]
    cmd += ["-c:a", "libmp3lame", str(out_mp3.resolve())]
    subprocess.run(cmd, check=True)

