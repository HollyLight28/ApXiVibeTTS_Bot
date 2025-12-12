import asyncio
from types import SimpleNamespace

import pytest

import bot as botmod


class FakeMessage:
    def __init__(self):
        self.replied_texts: list[str] = []
        self.edits: list[str] = []
        self.sent_audios: int = 0

    async def reply_text(self, text: str, reply_markup=None):  # noqa: ARG002
        self.replied_texts.append(text)
        return self

    async def edit_text(self, text: str):
        self.edits.append(text)

    async def reply_audio(self, audio, caption=None, title=None):  # noqa: D401, ARG002
        self.sent_audios += 1


class FakeQuery:
    def __init__(self):
        self.data = "SPEAK"
        self.id = 1
        self.message = FakeMessage()

    async def answer(self):
        return None


class FakeUpdateSpeak:
    def __init__(self):
        self.callback_query = FakeQuery()


class FakeContext:
    def __init__(self):
        self.user_data = {"last_bot_reply": "Привіт друже"}


def test_speak_selected_shows_progress(monkeypatch: pytest.MonkeyPatch):
    class FakeTTS:
        def __init__(self, model: str | None = None):  # noqa: ARG002
            pass
        def generate_pcm(self, text: str, voice_name: str = "Kore"):  # noqa: ARG002
            return b"\x00\x00"

    async def fake_acquire():
        return None

    def fake_merge(wavs, out_mp3, title=None, artist=None):  # noqa: ARG002
        out_mp3.parent.mkdir(parents=True, exist_ok=True)
        out_mp3.write_bytes(b"ID3")

    def fake_split(text: str, max_chars: int = 7000):  # noqa: ARG002
        return ["a", "b"]

    monkeypatch.setattr(botmod, "GeminiTTSClient", FakeTTS)
    monkeypatch.setattr(botmod.TTS_LIMITER, "acquire", fake_acquire)
    monkeypatch.setattr("app.audio_utils.merge_wavs_to_mp3_ffmpeg", fake_merge)
    monkeypatch.setattr("app.chunking.split_text_into_chunks", fake_split)

    update = FakeUpdateSpeak()
    context = FakeContext()

    asyncio.run(botmod.speak_selected(update, context))

    msgs = update.callback_query.message.replied_texts
    assert msgs and msgs[0].startswith("⏳ Озвучую відповідь")
    edits = update.callback_query.message.edits
    assert any("🔊 Озвучую чанк" in e for e in edits)
    assert any("🧩 Склеюю аудіо" in e for e in edits)


class FakeBot:
    def __init__(self):
        self.actions: list[tuple[int, str]] = []
    async def send_chat_action(self, chat_id: int, action: str):
        self.actions.append((chat_id, action))


class FakeMessageChat(FakeMessage):
    def __init__(self):
        super().__init__()
        self.chat = SimpleNamespace(id=123)
        self.text = "Привіт друже, як справи?"


class FakeUpdateChat:
    def __init__(self):
        self.message = FakeMessageChat()
        self.effective_chat = SimpleNamespace(id=123)


class FakeContextChat:
    def __init__(self):
        self.user_data = {"mode": "chat"}
        self.bot = FakeBot()


def test_handle_text_chat_progress(monkeypatch: pytest.MonkeyPatch):
    class FakeTextClient:
        def __init__(self, model: str | None = None):  # noqa: ARG002
            pass
        def generate_text(self, prompt: str, history=None):  # noqa: ARG002
            return "Відповідь"

    async def fake_acquire():
        return None

    monkeypatch.setattr(botmod, "GeminiTextClient", FakeTextClient)
    monkeypatch.setattr(botmod, "ddg_instant_answer", lambda q: [])
    monkeypatch.setattr(botmod.CHAT_LIMITER, "acquire", fake_acquire)

    update = FakeUpdateChat()
    context = FakeContextChat()

    asyncio.run(botmod.handle_text(update, context))

    msgs = update.message.replied_texts
    assert msgs and msgs[0].startswith("⏳ Генерую відповідь")
    assert any(m == "Відповідь" for m in msgs)
    assert context.bot.actions and context.bot.actions[0][1]
