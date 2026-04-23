"bot/states/broadcast_states.py"

from aiogram.fsm.state import State, StatesGroup

class BroadcastTargetSelection(StatesGroup):
    SELECTING_TARGETS = State()
    CONFIRMING_BROADCAST = State()
