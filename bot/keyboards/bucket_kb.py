from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import BucketPage, BucketSelect, ContentItemAction
from bot.keyboards.menu_kb import MENU_BTN
from bot.keyboards.pagination_kb import build_paginator_buttons
from bot.models.content_item import ContentBucket

def build_bucket_panel(bucket_name: str, items, page: int, total_pages: int) -> InlineKeyboardMarkup:
    bucket = ContentBucket(bucket_name)
    return build_content_list(items, bucket, page, total_pages)

def build_bucket_list() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buckets = [
        ("📝 Drafts",     ContentBucket.DRAFTS),
        ("📅 Scheduled",  ContentBucket.SCHEDULED),
        ("✅ Published",  ContentBucket.PUBLISHED),
        ("🗄 Archive",    ContentBucket.ARCHIVE),
    ]
    for text, bucket in buckets:
        builder.button(text=text, callback_data=BucketSelect(bucket=bucket).pack())
    builder.adjust(2)
    builder.row(MENU_BTN)
    return builder.as_markup()

def build_content_list(items, bucket: ContentBucket, page: int, total_pages: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = (item.text[:30] + "…") if item.text and len(item.text) > 30 else (item.text or "No text")
        builder.row(
            InlineKeyboardButton(
                text=title,
                callback_data=ContentItemAction(item_id=str(item.id), action="view").pack(),
            )
        )
    if total_pages > 1:
        paginator = build_paginator_buttons(BucketPage, {"bucket": bucket.value}, page, total_pages)
        builder.row(*paginator)
    builder.row(MENU_BTN)
    return builder.as_markup()
