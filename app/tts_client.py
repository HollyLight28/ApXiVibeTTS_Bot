from __future__ import annotations

import base64
import os

from google import genai
from google.genai import types


class GeminiTTSClient:
    # Клієнт для генерації PCM аудіо з тексту через Gemini TTS
    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash-preview-tts"):
        key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if key:
            self.client = genai.Client(api_key=key)
        else:
            self.client = genai.Client()
        self.model = model

    def generate_pcm(self, text: str, voice_name: str = "Kore") -> bytes:
        # Викликаємо TTS з відповідною конфігурацією голосу
        response = self.client.models.generate_content(
            model=self.model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                    )
                ),
            ),
        )
        candidates = getattr(response, "candidates", [])
        if not candidates:
            raise RuntimeError("Порожня відповідь від Gemini TTS")

        content = getattr(candidates[0], "content", None)
        parts = getattr(content, "parts", []) if content is not None else []
        if not parts:
            raise RuntimeError("Немає аудіо-даних у відповіді")

        inline_data = getattr(parts[0], "inline_data", None)
        data = getattr(inline_data, "data", None)
        if data is None:
            raise RuntimeError("Немає поля data у inline_data")

        # Бібліотека повертає або bytes, або base64-рядок. Обробляємо обидва варіанти
        if isinstance(data, str):
            return base64.b64decode(data)
        if isinstance(data, bytes):
            return data
        raise TypeError("Непідтримуваний тип даних аудіо")

