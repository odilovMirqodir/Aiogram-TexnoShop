from aiogram.fsm.state import StatesGroup, State


class Royxat(StatesGroup):
    ism = State()
    phone_number = State()
    users_birth_date = State()
