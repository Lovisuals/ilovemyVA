"bot/keyboards/pagination_kb.py"

from typing import List
from aiogram.types import InlineKeyboardButton
from bot.callbacks import Noop

def build_paginator_buttons(callback_prefix: str, page: int, total_pages: int) -> List[InlineKeyboardButton]:
    buttons = []
    
    # Left
    if page > 1:
        buttons.append(InlineKeyboardButton(text="«", callback_data=f"{callback_prefix}:{page - 1}"))
    else:
        buttons.append(InlineKeyboardButton(text=" ", callback_data=Noop().pack()))
        
    # Center
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data=Noop().pack()))
    
    # Right
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="»", callback_data=f"{callback_prefix}:{page + 1}"))
    else:
        buttons.append(InlineKeyboardButton(text=" ", callback_data=Noop().pack()))
        
    return buttons
