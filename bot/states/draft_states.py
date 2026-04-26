from aiogram.fsm.state import State, StatesGroup

class DraftCreation(StatesGroup):
    WAITING_SUBJECT = State()
    WAITING_BODY = State()
    CHOOSING_ACTION = State()
    CHOOSING_SCHED_TYPE = State()
    CHOOSING_TIME = State()
    CHOOSING_MULTIPLE_TIMES = State()
    ENTERING_CUSTOM_TIME = State()
    CHOOSING_DAYS = State()
    ENTERING_DATETIME = State()
    SELECTING_TARGETS = State()

class DraftEditing(StatesGroup):
    SELECTING_FIELD = State()
    EDITING_TEXT = State()
    EDITING_MEDIA = State()
    EDITING_TAGS = State()
