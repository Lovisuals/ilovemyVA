from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.callbacks import BucketPage, BucketSelect, ContentItemAction
from bot.models.content_item import ContentBucket
from bot.keyboards.pagination_kb import build_paginator_buttons

def build_bucket_list() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buckets = [
        ("📝 Drafts", ContentBucket.DRAFTS),
        ("📅 Scheduled", ContentBucket.SCHEDULED),
        ("✅ Published", ContentBucket.PUBLISHED),
        ("🗄 Archive", ContentBucket.ARCHIVE),
    ]
    for text, bucket in buckets:
        builder.button(text=text, callback_data=BucketSelect(bucket=bucket).pack())
    builder.adjust(2)
    return builder.as_markup()

def build_content_list(items, bucket: ContentBucket, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = (item.text[:30] + "...") if item.text and len(item.text) > 30 else (item.text or "No text")
        builder.row(
            InlineKeyboardButton(
                text=title, 
                callback_data=ContentItemAction(item_id=str(item.id), action="view").pack()
            )
        )
    if total_pages > 1:
        paginator = build_paginator_buttons(BucketPage, {"bucket": bucket.value}, page, total_pages)
        builder.row(*paginator)
    return builder.as_markup()
