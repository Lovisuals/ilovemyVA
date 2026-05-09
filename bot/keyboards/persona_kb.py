from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import NavData, PersonaAction
from bot.keyboards.menu_kb import MENU_BTN
from bot.models.persona import BotPersona
def build_persona_list(personas: List[BotPersona]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in personas:
        label = f"{'' if p.is_active else '○'} {p.name}" + (f" · {p.title}" if p.title else "")
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=PersonaAction(persona_id=str(p.id), action="view").pack(),
            )
        )
    builder.row(
        InlineKeyboardButton(text=" New Persona", callback_data=NavData(section="persona_new").pack())
    )
    builder.row(MENU_BTN)
    return builder.as_markup()
def build_persona_actions(persona_id: str, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_active:
        builder.button(
            text=" Activate",
            callback_data=PersonaAction(persona_id=persona_id, action="activate").pack(),
        )
    builder.button(
        text=" Delete",
        callback_data=PersonaAction(persona_id=persona_id, action="delete").pack(),
    )
    builder.adjust(2 if not is_active else 1)
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=NavData(section="persona").pack()),
        MENU_BTN,
    )
    return builder.as_markup()
