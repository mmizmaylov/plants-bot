import asyncio
import base64
import logging
import os
import random

from dotenv import load_dotenv
from telegram import Update, Message
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from app.vision_providers.openai_provider import analyze_plant
from app.prompt import build_system_prompt
from app.formatting import format_plant_reply, format_error_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Варианты сообщений о загрузке
LOADING_MESSAGES = [
    "🤔 Анализирую растение...",
    "🔍 Изучаю листья и стебель...",
    "⚡ Обрабатываю изображение...",
    "🧠 Определяю вид...",
    "📊 Сверяюсь с базой знаний...",
    "🔄 Анализирую характеристики...",
    "⏳ Секундочку...",
    "🌿 Распознаю растение...",
]

async def send_loading_message(update: Update) -> Message | None:
    """Отправляет случайное сообщение о загрузке"""
    if not update.message:
        return None
    
    try:
        loading_text = random.choice(LOADING_MESSAGES)
        loading_message = await update.message.reply_text(loading_text)
        return loading_message
    except Exception as e:
        logger.exception("Failed to send loading message: %s", e)
        return None

async def delete_loading_message(loading_message: Message | None) -> None:
    """Удаляет временное сообщение о загрузке"""
    if loading_message:
        try:
            await loading_message.delete()
        except Exception as e:
            logger.exception("Failed to delete loading message: %s", e)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    greeting = (
        "🌿 Привет! Я бот для распознавания растений!\n\n"
        "Пришлите мне:\n"
        "📸 **Фото растения** — я определю его название и расскажу о нём\n"
        "✍️ **Описание растения** — например, \"красивый цветок с белыми лепестками\"\n"
        "📸+✍️ **Фото с описанием** — для более точного анализа\n\n"
        "Я расскажу вам интересные факты о растении и дам советы по уходу! 🌱"
    )
    await update.message.reply_text(greeting, parse_mode=ParseMode.MARKDOWN)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message is not None
    
    # Отправляем сообщение о загрузке
    loading_message = await send_loading_message(update)
    
    try:
        # Получаем текст подписи к фото (если есть)
        photo_caption = (update.message.caption or "").strip()
        
        # Download the highest resolution photo
        try:
            photo = update.message.photo[-1]
            file = await photo.get_file()
            buf = await file.download_as_bytearray()
            image_b64 = base64.b64encode(bytes(buf)).decode("utf-8")
            image_data_url = f"data:image/jpeg;base64,{image_b64}"
        except Exception as e:
            logger.exception("Failed to download photo: %s", e)
            await delete_loading_message(loading_message)
            await update.message.reply_text("Не удалось скачать фото. Попробуйте ещё раз.")
            return

        # Call vision provider with photo and optional text description
        try:
            system_prompt = build_system_prompt()
            analysis = await analyze_plant(
                image_data_url=image_data_url, 
                system_prompt=system_prompt,
                text_description=photo_caption if photo_caption else None
            )
        except Exception as e:
            logger.exception("Vision analyze error: %s", e)
            await delete_loading_message(loading_message)
            await update.message.reply_text("Не удалось проанализировать фото. Попробуйте ещё раз.")
            return

        # Удаляем сообщение о загрузке перед отправкой результата
        await delete_loading_message(loading_message)
        
        # Process the result
        await _process_plant_analysis(update, analysis)
        
    except Exception as e:
        # В случае любой ошибки удаляем сообщение о загрузке
        await delete_loading_message(loading_message)
        logger.exception("Unexpected error in handle_photo: %s", e)
        await update.message.reply_text("Произошла ошибка при обработке фото. Попробуйте ещё раз.")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Анализирует текстовое описание как растение"""
    assert update.message is not None
    
    text_description = (update.message.text or "").strip()
    
    # Игнорируем команды
    if text_description.startswith('/'):
        return
    
    # Отправляем сообщение о загрузке
    loading_message = await send_loading_message(update)
    
    try:
        # Call vision provider with text description only
        system_prompt = build_system_prompt()
        analysis = await analyze_plant(
            system_prompt=system_prompt,
            text_description=text_description
        )
        
        # Удаляем сообщение о загрузке перед отправкой результата
        await delete_loading_message(loading_message)
        
        # Process the result
        await _process_plant_analysis(update, analysis)
        
    except Exception as e:
        # В случае ошибки удаляем сообщение о загрузке
        await delete_loading_message(loading_message)
        logger.exception("Text analyze error: %s", e)
        await update.message.reply_text("Не удалось проанализировать описание. Попробуйте ещё раз.")


async def _process_plant_analysis(update: Update, analysis: dict) -> None:
    """Общая логика обработки результата анализа растения"""
    assert update.message is not None
    
    # Extract values
    plant_name = analysis.get("plant_name") or "Неизвестное растение"
    scientific_name = analysis.get("scientific_name")
    family = analysis.get("family")
    description = analysis.get("description") or "Информация недоступна"
    care_tips = analysis.get("care_tips")
    fun_facts = analysis.get("fun_facts")
    is_toxic = analysis.get("is_toxic")
    difficulty = analysis.get("difficulty")
    low_quality = analysis.get("low_quality", False)

    if low_quality:
        error_msg = format_error_message(
            "Сложно распознать растение на фото или по описанию"
        )
        await update.message.reply_text(error_msg)
        return

    reply = format_plant_reply(
        plant_name=plant_name,
        scientific_name=scientific_name,
        family=family,
        description=description,
        care_tips=care_tips,
        fun_facts=fun_facts,
        is_toxic=is_toxic,
        difficulty=difficulty,
    )

    await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🌿 **Как пользоваться ботом:**\n\n"
        "📸 **Отправьте фото растения** — я определю его и расскажу о нём\n"
        "✍️ **Опишите растение текстом** — я постараюсь его определить\n"
        "📸+✍️ **Фото с подписью** — для лучшего результата\n\n"
        "**Команды:**\n"
        "/start — начать работу с ботом\n"
        "/help — показать эту справку\n\n"
        "Я расскажу вам:\n"
        "• Название растения (обычное и научное)\n"
        "• Семейство растения\n"
        "• Описание и характеристики\n"
        "• Советы по уходу\n"
        "• Интересные факты\n"
        "• Информацию о токсичности\n"
        "• Сложность ухода\n\n"
        "🌱 Удачного изучения растений!"
    )
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == "__main__":
    main() 