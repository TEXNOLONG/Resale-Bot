"""
Вспомогательные утилиты для работы с сообщениями Telegram.
"""

from aiogram.types import Message


async def safe_edit_text(message: Message, text: str, reply_markup=None, parse_mode: str = None):
    """
    Безопасное редактирование сообщения.
    - Если сообщение текстовое — edit_text.
    - Если сообщение с фото (caption) — edit_caption.
    - Fallback: удалить старое и отправить новое текстовое сообщение.
    """
    kwargs = {}
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup
    if parse_mode is not None:
        kwargs["parse_mode"] = parse_mode

    # Попытка 1: обычное text-сообщение
    try:
        await message.edit_text(text, **kwargs)
        return
    except Exception:
        pass

    # Попытка 2: фото-сообщение с подписью (caption)
    try:
        await message.edit_caption(caption=text, **kwargs)
        return
    except Exception:
        pass

    # Fallback: удалить и отправить новое текстовое сообщение
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer(text, **kwargs)
