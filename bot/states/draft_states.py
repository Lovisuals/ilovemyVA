"bot/states/draft_states.py"

from aiogram.fsm.state import State, StatesGroup

class DraftCreation(StatesGroup):
    WAITING_CONTENT = State()
    CONFIRMING = State()

class DraftEditing(StatesGroup):
    SELECTING_FIELD = State()
    EDITING_TEXT = State()
    EDITING_MEDIA = State()
    EDITING_TAGS = State()
