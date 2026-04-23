"bot/keyboards/pagination_kb.py"

from typing import List, Type, Dict, Any
from aiogram.types import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from bot.callbacks import Noop

def build_paginator_buttons(
    callback_class: Type[CallbackData],
    params: Dict[str, Any],
    page: int,
    total_pages: int
) -> List[InlineKeyboardButton]:
    buttons = []

    # Left
    if page > 1:
        prev_params = params.copy()
        prev_params["page"] = page - 1
        buttons.append(InlineKeyboardButton(
            text="«",
            callback_data=callback_class(**prev_params).pack()
        ))
    else:
        buttons.append(InlineKeyboardButton(text=" ", callback_data=Noop().pack()))

    # Center
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=Noop().pack()))

    # Right
    if page < total_pages:
        next_params = params.copy()
        next_params["page"] = page + 1
        buttons.append(InlineKeyboardButton(
            text="»",
            callback_data=callback_class(**next_params).pack()
        ))
    else:
        buttons.append(InlineKeyboardButton(text=" ", callback_data=Noop().pack()))

    return buttons
