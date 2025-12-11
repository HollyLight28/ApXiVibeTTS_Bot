from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.audio_utils import merge_wavs_to_mp3_ffmpeg, write_wave_from_pcm
from app.chunking import split_text_into_chunks
from app.title import infer_title
from app.tts_client import GeminiTTSClient
from app.ui import get_main_keyboard_labels

# Налаштовуємо логування в консоль
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("ApXiVibeTTS")


# Константи
ALLOWED_VOICES = ("Kore", "Aoede", "Puck", "Charon")
MODEL_ID = "gemini-2.5-flash-preview-tts"
TEMP_DIR = Path("temp_audio")
MIN_LEN = 10
MAX_LEN = 50_000


def get_env_token() -> str:
    # Завантажуємо змінні середовища із .env, якщо доступно
    if load_dotenv:
        load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Не знайдено TELEGRAM_BOT_TOKEN у .env або змінних середовища")
    return token


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Привітання та коротка інструкція
    text = (
        "👋 Вітаю, бро! Я озвучу твій текст через Gemini TTS.\n\n"
        "Надішли мені текст повідомлення, а я поверну MP3.\n"
        "Команди:\n"
        "• /voice — вибір голосу (Kore, Aoede, Puck, Charon)\n"
        "• /help — детальна допомога"
    )
    keyboard = ReplyKeyboardMarkup(get_main_keyboard_labels(), resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Детальна інструкція користувачу
    text = (
        "ℹ️ Як користуватись:\n"
        "1) Надішли текст повідомлення (10–50 000 символів).\n"
        "2) Я розіб'ю його на чанки по реченнях (якщо > 7000).\n"
        "3) Згенерую аудіо через Gemini TTS і склею в MP3.\n"
        "4) Відправлю тобі MP3 і видалю тимчасові файли.\n\n"
        "⚙️ Поради:\n"
        "• Обери голос у /voice. За замовчуванням — Kore.\n"
        "• Для великих текстів я показую прогрес у повідомленні."
    )
    await update.message.reply_text(text)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = ReplyKeyboardMarkup(get_main_keyboard_labels(), resize_keyboard=True)
    await update.message.reply_text("📎 Клавіатура показана", reply_markup=keyboard)


def _voice_keyboard() -> InlineKeyboardMarkup:
    # Створюємо інлайн-клавіатуру для вибору голосу
    buttons = [
        [InlineKeyboardButton("Kore", callback_data="VOICE:Kore"), InlineKeyboardButton("Aoede", callback_data="VOICE:Aoede")],
        [InlineKeyboardButton("Puck", callback_data="VOICE:Puck"), InlineKeyboardButton("Charon", callback_data="VOICE:Charon")],
    ]
    return InlineKeyboardMarkup(buttons)


def _style_keyboard() -> InlineKeyboardMarkup:
    # Інлайн-клавіатура для вибору стилю/темпу
    buttons = [
        [
            InlineKeyboardButton("Нейтрально", callback_data="STYLE:Neutral"),
            InlineKeyboardButton("Повільно", callback_data="STYLE:Slow"),
        ],
        [
            InlineKeyboardButton("Швидко", callback_data="STYLE:Fast"),
            InlineKeyboardButton("Емоційно", callback_data="STYLE:Emotional"),
        ],
        [
            InlineKeyboardButton("Новини", callback_data="STYLE:News"),
            InlineKeyboardButton("Аудіокнига", callback_data="STYLE:Audiobook"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Відображаємо інлайн-кнопки для вибору голосу
    await update.message.reply_text("🎙️ Обери голос:", reply_markup=_voice_keyboard())


async def style_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Інлайн-кнопки стилю/темпу
    await update.message.reply_text("🎚️ Обери стиль/темп:", reply_markup=_style_keyboard())


async def voice_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обробляємо вибір голосу з інлайн-кнопки
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("VOICE:"):
        voice_name = data.split(":", 1)[1]
        if voice_name in ALLOWED_VOICES:
            context.user_data["voice"] = voice_name
            await query.edit_message_text(f"✅ Голос встановлено: {voice_name}")
        else:
            await query.edit_message_text("❌ Невідомий голос")


async def style_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Обробляємо вибір стилю
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    if data.startswith("STYLE:"):
        style_key = data.split(":", 1)[1]
        context.user_data["style"] = style_key
        await query.edit_message_text(f"✅ Стиль встановлено: {style_key}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Основна логіка: валідати → повідомити прогрес → TTS → склейка → відправка MP3 → очистка
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Валідація довжини
    if len(text) < MIN_LEN:
        await update.message.reply_text("❌ Занадто короткий текст")
        return
    if len(text) > MAX_LEN:
        await update.message.reply_text("❌ Занадто довгий текст")
        return

    # Прогрес-повідомлення
    progress_msg = await update.message.reply_text("⏳ Генерую аудіо...")

    # Обраний голос
    voice_name = context.user_data.get("voice", "Kore")
    if voice_name not in ALLOWED_VOICES:
        voice_name = "Kore"

    # Розбиття на чанки
    chunks = split_text_into_chunks(text, max_chars=7000)
    total = len(chunks) or 1

    # Ініціалізація клієнта Gemini
    tts = GeminiTTSClient(model=MODEL_ID)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    wav_paths: list[Path] = []

    try:
        # Генерація аудіо для кожного чанку
        for idx, chunk in enumerate(chunks, start=1):
            await progress_msg.edit_text(f"🔊 Генерую чанк {idx}/{total}…")

            # Синхронний виклик у фоні, щоб не блокувати event loop
            final_text = chunk
            pcm_bytes = await asyncio.to_thread(tts.generate_pcm, final_text, voice_name)

            wav_path = TEMP_DIR / f"chunk_{idx}.wav"
            await asyncio.to_thread(write_wave_from_pcm, wav_path, pcm_bytes)
            wav_paths.append(wav_path)

        # Склейка WAV у один MP3 через ffmpeg (без pydub, сумісно з Python 3.13)
        await progress_msg.edit_text("🧩 Склеюю аудіо…")
        out_mp3 = TEMP_DIR / f"tts_{update.message.message_id}.mp3"
        audio_title = infer_title(text)
        await asyncio.to_thread(
            merge_wavs_to_mp3_ffmpeg,
            wav_paths,
            out_mp3,
            audio_title,
            "ApXiVibeTTS",
        )

        await progress_msg.edit_text("✅ Готово! Відправляю MP3…")
        # Відправляємо MP3 користувачу
        with out_mp3.open("rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption=f"🎧 Голос: {voice_name}",
                title=audio_title,
            )

    except Exception as e:
        log.exception("Помилка генерації аудіо: %s", e)
        try:
            await progress_msg.edit_text("⚠️ Помилка, спробуй пізніше")
        except Exception as cleanup_err:
            log.debug("Не вдалось оновити повідомлення про помилку: %s", cleanup_err)
    finally:
        # Очищення тимчасових файлів
        for p in wav_paths:
            try:
                p.unlink(missing_ok=True)
            except Exception as rm_err:
                log.debug("Не вдалось видалити тимчасовий WAV: %s", rm_err)

        # Видаляємо MP3 після відправки, щоб не засмічувати диск
        try:
            for mp3 in TEMP_DIR.glob("tts_*.mp3"):
                mp3.unlink(missing_ok=True)
        except Exception as rm_err:
            log.debug("Не вдалось видалити тимчасовий MP3: %s", rm_err)


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("♻️ Скинуто налаштування", reply_markup=ReplyKeyboardRemove())


async def post_init(application: Application) -> None:
    # Меню команд Telegram (щоб не вводити вручну)
    await application.bot.set_my_commands(
        [
            BotCommand("start", "Привітання та клавіатура"),
            BotCommand("voice", "Вибір голосу"),
            BotCommand("help", "Допомога"),
            BotCommand("menu", "Показати клавіатуру"),
            BotCommand("reset", "Скинути налаштування та прибрати клавіатуру"),
        ]
    )


def build_app() -> Application:
    # Будуємо асинхронний Telegram Application
    token = get_env_token()
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("voice", voice))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("reset", reset_command))
    # Обробка натиснення кнопок з головної клавіатури
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🎙️ Обрати голос$"), voice))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^ℹ️ Допомога$"), help_command))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^🎚️ Стиль/Темп$"), style_menu))
    app.add_handler(CallbackQueryHandler(voice_selected, pattern=r"^VOICE:"))
    app.add_handler(CallbackQueryHandler(style_selected, pattern=r"^STYLE:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return app


def get_webhook_config() -> tuple[str, int] | None:
    url = os.environ.get("WEBHOOK_URL")
    if not url:
        return None
    port_str = os.environ.get("PORT") or os.environ.get("WEBHOOK_PORT") or "8080"
    try:
        port = int(port_str)
    except Exception:
        port = 8080
    return (url, port)


def main() -> None:
    app = build_app()
    cfg = get_webhook_config()
    if cfg is not None:
        url, port = cfg
        log.info("Запускаю вебхук…")
        app.run_webhook(port=port, webhook_url=url, drop_pending_updates=True)
    else:
        log.info("Запускаю поллінг…")
        app.bot.delete_webhook(drop_pending_updates=True)
        app.run_polling(close_loop=False, drop_pending_updates=True)


if __name__ == "__main__":
    main()

