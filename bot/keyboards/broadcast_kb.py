"bot/keyboards/broadcast_kb.py"

from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import BroadcastToggle, BroadcastDone

def build_target_selector(item_id: str, targets: List[Dict], selected_ids: List[int]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for target in targets:
        is_selected = target["chat_id"] in selected_ids
        icon = "☑️" if is_selected else "⬜️"
        builder.button(
            text=f"{icon} {target['name']}",
            callback_data=BroadcastToggle(item_id=item_id, chat_id=str(target["chat_id"]))
        )
        
    builder.adjust(1)
    
    builder.row(
        builder.button(
            text=f"✅ Done ({len(selected_ids)} selected)",
            callback_data=BroadcastDone(item_id=item_id)
        ).button
    )
    
    return builder.as_markup()
