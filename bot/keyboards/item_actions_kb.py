from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import ContentItemAction, ItemSchedule
from bot.keyboards.menu_kb import MENU_BTN
from bot.models.content_item import ContentBucket

def _btn(label: str, item_id: str, action: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=label,
        callback_data=ContentItemAction(item_id=item_id, action=action).pack(),
    )

def build_item_actions(item_id: str, bucket: ContentBucket) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if bucket == ContentBucket.DRAFTS:
        builder.row(
            InlineKeyboardButton(text="✍️ Edit",      callback_data=f"item_ed:{item_id}"),
            InlineKeyboardButton(text="📅 Schedule",  callback_data=ItemSchedule(item_id=item_id).pack()),
        )
        builder.row(
            InlineKeyboardButton(text="🚀 Broadcast", callback_data=f"item_br:{item_id}"),
            _btn("🗑 Delete", item_id, "delete"),
        )
    elif bucket == ContentBucket.SCHEDULED:
        builder.row(
            InlineKeyboardButton(text="🕒 Change Time", callback_data=ItemSchedule(item_id=item_id).pack()),
            _btn("❌ Unschedule", item_id, "unschedule"),
        )
        builder.row(
            _btn("🗑 Delete", item_id, "delete"),
        )
    elif bucket == ContentBucket.PUBLISHED:
        builder.row(
            InlineKeyboardButton(text="♻️ Repost", callback_data=f"item_br:{item_id}"),
            _btn("🗑 Delete", item_id, "delete"),
        )
    else:
        builder.row(_btn("🗑 Delete", item_id, "delete"))

    builder.row(_btn("← Back to List", item_id, "back"))
    builder.row(MENU_BTN)
    return builder.as_markup()
