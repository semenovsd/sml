from aiogram.dispatcher.filters.state import State, StatesGroup


class EditAlbum(StatesGroup):
    EditName = State()


class Mailing(StatesGroup):
    Text = State()
    Language = State()
