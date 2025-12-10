from __future__ import annotations

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

