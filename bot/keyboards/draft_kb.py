from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import (
    DayToggle, PostAction, RetryBroadcast, SchedType, TargetToggle, TimeSlot, MultiTimeToggle
)
from bot.keyboards.menu_kb import MENU_BTN
from bot.config import settings


def _editor_url() -> Optional[str]:
    if settings.bot.webhook_url:
        return f"{settings.bot.webhook_url}/static/editor.html"
    return None

_DAYS = [
    ("Mo", "mo"), ("Tu", "tu"), ("We", "we"), ("Th", "th"),
    ("Fr", "fr"), ("Sa", "sa"), ("Su", "su"),
]

_TIME_SLOTS = [
    ("⏱ Multiple Times", "always"),
    ("06:00",     "0600"),
    ("09:00",     "0900"),
    ("12:00",     "1200"),
    ("15:00",     "1500"),
    ("18:00",     "1800"),
    ("21:00",     "2100"),
    ("⌨️ Custom…", "custom"),
]


def _cancel_btn() -> InlineKeyboardButton:
    return InlineKeyboardButton(text="✕ Cancel", callback_data=PostAction(action="cancel").pack())


def build_step1_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    url = _editor_url()
    if url:
        builder.row(
            InlineKeyboardButton(text="📝 Open Editor", web_app=WebAppInfo(url=url))
        )
        builder.row(
            InlineKeyboardButton(text="⌨️ Type Instead", callback_data=PostAction(action="type_mode").pack()),
            _cancel_btn(),
        )
    else:
        builder.row(_cancel_btn())
    return builder.as_markup()


def build_step2_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    url = _editor_url()
    if url:
        builder.row(
            InlineKeyboardButton(text="📝 Open Editor", web_app=WebAppInfo(url=url))
        )
    builder.row(
        InlineKeyboardButton(text="✏️ Edit Subject", callback_data=PostAction(action="edit_subj").pack()),
        _cancel_btn(),
    )
    return builder.as_markup()


def build_action_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚡ Post Now",   callback_data=PostAction(action="now").pack()),
        InlineKeyboardButton(text="⏰ Schedule",   callback_data=PostAction(action="sched").pack()),
    )
    builder.row(
        InlineKeyboardButton(text="💾 Save Draft", callback_data=PostAction(action="draft").pack()),
    )
    url = _editor_url()
    if url:
        builder.row(
            InlineKeyboardButton(text="📝 Edit in App",  web_app=WebAppInfo(url=url)),
            InlineKeyboardButton(text="✏️ Subject",      callback_data=PostAction(action="edit_subj").pack()),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="✏️ Edit Subject", callback_data=PostAction(action="edit_subj").pack()),
            InlineKeyboardButton(text="✏️ Edit Body",    callback_data=PostAction(action="edit_body").pack()),
        )
    builder.row(_cancel_btn())
    return builder.as_markup()


def build_sched_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Recurring", callback_data=SchedType(sched_type="recurring").pack()),
        InlineKeyboardButton(text="📅 One-Time",  callback_data=SchedType(sched_type="one_time").pack()),
    )
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=SchedType(sched_type="back").pack()),
    )
    return builder.as_markup()


def build_time_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, slot in _TIME_SLOTS:
        builder.button(text=label, callback_data=TimeSlot(slot=slot).pack())
    builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=TimeSlot(slot="back").pack()),
    )
    return builder.as_markup()


def build_multi_time_kb(selected_slots: List[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h in range(24):
        slot = f"{h:02d}00"
        label = f"{h:02d}:00"
        icon = "✅" if slot in selected_slots else "○"
        builder.button(text=f"{icon} {label}", callback_data=MultiTimeToggle(action="toggle", slot=slot).pack())
    builder.adjust(4)
    count = len(selected_slots)
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=MultiTimeToggle(action="back").pack()),
        InlineKeyboardButton(
            text=f"Continue → ({count})" if count else "Continue →",
            callback_data=MultiTimeToggle(action="confirm").pack()
        ),
    )
    return builder.as_markup()


def build_custom_time_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=TimeSlot(slot="back").pack()),
    )
    return builder.as_markup()


def build_datetime_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=SchedType(sched_type="back").pack()),
    )
    return builder.as_markup()


def build_day_kb(selected: List[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for label, key in _DAYS:
        icon = "✅" if key in selected else "○"
        builder.button(text=f"{icon} {label}", callback_data=DayToggle(day=key).pack())
    builder.adjust(4, 3)
    builder.row(
        InlineKeyboardButton(text="Every Day",  callback_data=DayToggle(day="everyday").pack()),
        InlineKeyboardButton(text="Weekdays",   callback_data=DayToggle(day="weekdays").pack()),
        InlineKeyboardButton(text="Weekends",   callback_data=DayToggle(day="weekends").pack()),
    )
    count = len(selected)
    builder.row(
        InlineKeyboardButton(text="← Back",             callback_data=DayToggle(day="back").pack()),
        InlineKeyboardButton(
            text=f"Continue → ({count}d)" if count else "Continue →",
            callback_data=DayToggle(day="confirm").pack(),
        ),
    )
    return builder.as_markup()


def build_target_kb(
    chats: list,
    selected_ids: List[int],
    confirm_label: str = "✅ Confirm",
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for chat in chats:
        icon = "✅" if chat.chat_id in selected_ids else "○"
        type_icon = "🔊" if chat.chat_type == "channel" else "👥"
        builder.button(
            text=f"{icon} {type_icon} {chat.title}",
            callback_data=TargetToggle(action="chat", chat_id=chat.chat_id).pack(),
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="☑️ All",  callback_data=TargetToggle(action="all",  chat_id=0).pack()),
        InlineKeyboardButton(text="☐ None", callback_data=TargetToggle(action="none", chat_id=0).pack()),
    )
    count = len(selected_ids)
    builder.row(
        InlineKeyboardButton(text="← Back", callback_data=TargetToggle(action="back", chat_id=0).pack()),
        InlineKeyboardButton(
            text=f"{confirm_label} ({count})" if count else confirm_label,
            callback_data=TargetToggle(action="confirm", chat_id=0).pack(),
        ),
    )
    return builder.as_markup()


def build_report_kb(has_failed: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_failed:
        builder.row(
            InlineKeyboardButton(
                text="🔄 Retry Failed",
                callback_data=RetryBroadcast().pack(),
            )
        )
    builder.row(MENU_BTN)
    return builder.as_markup()
