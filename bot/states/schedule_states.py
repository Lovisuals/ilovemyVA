"bot/states/schedule_states.py"

from aiogram.fsm.state import State, StatesGroup

class SchedulePicking(StatesGroup):
    PICKING_TIME = State()
    PICKING_CUSTOM_TIME = State()
    PICKING_RECURRENCE = State()
    CONFIRMING_SCHEDULE = State()
