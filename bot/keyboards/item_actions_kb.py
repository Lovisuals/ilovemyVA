from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ContentItemAction
from bot.models.content_item import ContentBucket

def build_item_actions(item_id: str, bucket: ContentBucket) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if bucket == ContentBucket.DRAFTS:
        builder.button(text="✍️ Edit", callback_data=ContentItemAction(item_id=item_id, action="edit").pack())
        builder.button(text="📅 Schedule", callback_data=ContentItemAction(item_id=item_id, action="schedule").pack())
        builder.button(text="🚀 Broadcast", callback_data=ContentItemAction(item_id=item_id, action="broadcast").pack())
    elif bucket == ContentBucket.SCHEDULED:
        builder.button(text="❌ Unschedule", callback_data=ContentItemAction(item_id=item_id, action="unschedule").pack())
    elif bucket == ContentBucket.PUBLISHED:
        builder.button(text="♻️ Repost", callback_data=ContentItemAction(item_id=item_id, action="repost").pack())
    builder.button(text="🗑 Delete", callback_data=ContentItemAction(item_id=item_id, action="delete").pack())
    builder.button(text="← Back", callback_data=ContentItemAction(item_id=item_id, action="back").pack())
    builder.adjust(2)
    return builder.as_markup()
