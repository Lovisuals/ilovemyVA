"bot/states/settings_states.py"

from aiogram.fsm.state import State, StatesGroup

class SettingsStates(StatesGroup):
    ADD_TARGET = State()
    SET_TIMEZONE = State()
