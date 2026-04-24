from aiogram.filters.callback_data import CallbackData

class BucketSelect(CallbackData, prefix="bucket_sel"):
    bucket: str

class BucketPage(CallbackData, prefix="bucket_pg"):
    bucket: str
    page: int

class ItemView(CallbackData, prefix="item_vw"):
    item_id: str

class ContentItemAction(CallbackData, prefix="item_ac"):
    item_id: str
    action: str

class ItemEdit(CallbackData, prefix="item_ed"):
    item_id: str

class ItemPreview(CallbackData, prefix="item_pr"):
    item_id: str

class ItemSchedule(CallbackData, prefix="item_sc"):
    item_id: str

class ItemBroadcast(CallbackData, prefix="item_br"):
    item_id: str

class ItemArchive(CallbackData, prefix="item_ar"):
    item_id: str

class ItemDelete(CallbackData, prefix="item_de"):
    item_id: str

class ConfirmYes(CallbackData, prefix="conf_y"):
    action: str
    target_id: str

class ConfirmNo(CallbackData, prefix="conf_n"):
    action: str
    target_id: str

class ScheduleTime(CallbackData, prefix="sch_t"):
    item_id: str
    time_str: str

class ScheduleCustom(CallbackData, prefix="sch_c"):
    item_id: str

class ScheduleRecurrence(CallbackData, prefix="sch_r"):
    item_id: str
    recurrence: str

class BroadcastToggle(CallbackData, prefix="brd_t"):
    item_id: str
    chat_id: str

class BroadcastDone(CallbackData, prefix="brd_d"):
    item_id: str

class OnboardGen(CallbackData, prefix="onb_g"):
    user_id: int

class UserAction(CallbackData, prefix="usr_a"):
    user_id: int
    action: str

class UserPage(CallbackData, prefix="usr_p"):
    page: int

class ModerationResolve(CallbackData, prefix="mod_r"):
    event_id: str
    resolution: str

class Noop(CallbackData, prefix="noop"):
    pass

class NavData(CallbackData, prefix="nav"):
    section: str

class PersonaAction(CallbackData, prefix="pers_a"):
    persona_id: str
    action: str

class FaqAction(CallbackData, prefix="faq_a"):
    entry_id: str
    action: str

class PostAction(CallbackData, prefix="pa"):
    action: str  # now | sched | draft | edit_subj | edit_body | cancel

class SchedType(CallbackData, prefix="st"):
    sched_type: str  # recurring | one_time | back

class TimeSlot(CallbackData, prefix="tsl"):
    slot: str  # always | 0600 | 0900 | 1200 | 1500 | 1800 | 2100 | custom | back

class DayToggle(CallbackData, prefix="dtg"):
    day: str  # mo|tu|we|th|fr|sa|su | everyday | weekdays | weekends | confirm | back

class TargetToggle(CallbackData, prefix="ttg"):
    action: str  # chat | all | none | confirm | back
    chat_id: int = 0

class RetryBroadcast(CallbackData, prefix="rbr"):
    pass
