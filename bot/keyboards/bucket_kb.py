"bot/keyboards/bucket_kb.py"

from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import BucketSelect, ItemView, BucketPage
from bot.models.content_item import ContentItem, ContentBucket
from bot.keyboards.pagination_kb import build_paginator_buttons
from bot.utils.preview import truncate_preview

def build_bucket_panel(
    active_bucket: str,
    items: List[ContentItem],
    page: int,
    total_pages: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Bucket Selector Row
    buckets = [
        (ContentBucket.DRAFTS.value, "📝"),
        (ContentBucket.SCHEDULED.value, "⏰"),
        (ContentBucket.PUBLISHED.value, "✅"),
        (ContentBucket.ARCHIVE.value, "📦")
    ]

    for bucket_name, icon in buckets:
        label = f"[{icon}]" if bucket_name == active_bucket else icon
        builder.button(
            text=label,
            callback_data=BucketSelect(bucket=bucket_name).pack()
        )

    builder.adjust(4)

    # Item Rows
    for item in items:
        preview = truncate_preview(item.text or "Media Item", 30)
        builder.row(
            InlineKeyboardButton(
                text=f"• {preview}",
                callback_data=ItemView(item_id=str(item.id)).pack()
            )
        )

    # Pagination Row
    if total_pages > 1:
        paginator = build_paginator_buttons(BucketPage, {"bucket": active_bucket}, page, total_pages)
        builder.row(*paginator)

    return builder.as_markup()
