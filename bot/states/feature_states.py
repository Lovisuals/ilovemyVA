from aiogram.fsm.state import State, StatesGroup


class PersonaCreation(StatesGroup):
    ENTERING_NAME = State()


class FaqCreation(StatesGroup):
    ENTERING_TRIGGER = State()
    ENTERING_RESPONSE = State()


class WelcomeSetup(StatesGroup):
    ENTERING_MESSAGE = State()
