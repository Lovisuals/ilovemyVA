from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import ContentItemAction
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
        builder.row(_btn("✍️ Edit", item_id, "edit"),      _btn("📅 Schedule", item_id, "schedule"))
        builder.row(_btn("🚀 Broadcast", item_id, "broadcast"), _btn("🗑 Delete", item_id, "delete"))
    elif bucket == ContentBucket.SCHEDULED:
        builder.row(_btn("❌ Unschedule", item_id, "unschedule"), _btn("🗑 Delete", item_id, "delete"))
    elif bucket == ContentBucket.PUBLISHED:
        builder.row(_btn("♻️ Repost", item_id, "repost"), _btn("🗑 Delete", item_id, "delete"))
    else:
        builder.row(_btn("🗑 Delete", item_id, "delete"))

    builder.row(_btn("← Back to List", item_id, "back"))
    builder.row(MENU_BTN)
    return builder.as_markup()
