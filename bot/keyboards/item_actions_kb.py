"bot/keyboards/item_actions_kb.py"

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import (
    ItemEdit, ItemPreview, ItemSchedule, 
    ItemBroadcast, ItemArchive, ItemDelete, 
    BucketSelect
)

def build_item_actions(item_id: str, bucket: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Row 1
    builder.button(text="✏️ Edit", callback_data=ItemEdit(item_id=item_id))
    builder.button(text="👁 Preview", callback_data=ItemPreview(item_id=item_id))
    builder.button(text="⏰ Schedule", callback_data=ItemSchedule(item_id=item_id))
    
    # Row 2
    builder.button(text="📡 Broadcast", callback_data=ItemBroadcast(item_id=item_id))
    builder.button(text="📦 Archive", callback_data=ItemArchive(item_id=item_id))
    builder.button(text="🗑 Delete", callback_data=ItemDelete(item_id=item_id))
    
    # Row 3
    builder.button(text="← Back", callback_data=BucketSelect(bucket=bucket))
    
    builder.adjust(3, 3, 1)
    return builder.as_markup()
