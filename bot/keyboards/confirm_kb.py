from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ConfirmYes, ConfirmNo
def build_confirm(action: str, target_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=" Yes", callback_data=ConfirmYes(action=action, target_id=target_id).pack())
    builder.button(text=" No", callback_data=ConfirmNo(action=action, target_id=target_id).pack())
    builder.adjust(2)
    return builder.as_markup()
