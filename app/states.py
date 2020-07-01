from aiogram.dispatcher.filters.state import State, StatesGroup


class EditWithdraw(StatesGroup):
    EditFullName = State()
    EditPhoneNumber = State()
    EditEmail = State()
    EditPassportNumber = State()
    EditCheck = State()


class Mailing(StatesGroup):
    Text = State()
    Language = State()
