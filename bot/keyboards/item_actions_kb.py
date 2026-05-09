from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import ContentItemAction, ItemSchedule, ItemEdit
from bot.keyboards.menu_kb import MENU_BTN
from bot.models.content_item import ContentBucket
from bot.utils.url_utils import get_editor_url
def _btn(label: str, item_id: str, action: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=label,
        callback_data=ContentItemAction(item_id=item_id, action=action).pack(),
    )
def build_item_actions(item_id: str, bucket: ContentBucket) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if bucket == ContentBucket.DRAFTS:
        builder.row(
            InlineKeyboardButton(text="Post Now", callback_data=f"item_br:{item_id}"),
            InlineKeyboardButton(text="Schedule", callback_data=ItemSchedule(item_id=item_id).pack()),
        )
        builder.row(
            InlineKeyboardButton(text="Edit", callback_data=ItemEdit(item_id=item_id).pack()),
            _btn("Delete", item_id, "delete"),
        )
    elif bucket == ContentBucket.SCHEDULED:
        builder.row(
            InlineKeyboardButton(text="Edit Content", callback_data=ItemEdit(item_id=item_id).pack()),
            InlineKeyboardButton(text="Change Time", callback_data=ItemSchedule(item_id=item_id).pack()),
        )
        url = get_editor_url()
        if url:
            builder.row(
                InlineKeyboardButton(text="Edit in App", web_app=WebAppInfo(url=f"{url}?item_id={item_id}"))
            )
        builder.row(
            _btn("Unschedule", item_id, "unschedule"),
            _btn("Delete", item_id, "delete"),
        )
    elif bucket == ContentBucket.PUBLISHED:
        builder.row(
            InlineKeyboardButton(text="Post Again", callback_data=f"item_br:{item_id}"),
            InlineKeyboardButton(text="Schedule", callback_data=ItemSchedule(item_id=item_id).pack()),
        )
        builder.row(
            _btn("Archive", item_id, "archive"),
            _btn("Delete", item_id, "delete"),
        )
    else:
        builder.row(_btn("Delete", item_id, "delete"))
    builder.row(_btn("Back to List", item_id, "back"))
    builder.row(MENU_BTN)
    return builder.as_markup()
