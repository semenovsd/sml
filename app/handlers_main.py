from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import User
from load_all import bot, dp


# /start
@dp.message_handler(CommandStart())
async def start_cmd_handler(message: types.Message, user: User):
    # TODO refact
    # Make keyboard for next step
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Начать', callback_data='main')]]
    )

    # If user subscriber
    # if user and user.subscribe and user.subscribe_end_date > datetime.now():
    if user:
        reply = 'Привет ;) Собрать ещё плейлистов? Начнём!'
    else:
        reply = 'Привет! Я помогу тебе собрать плейлисты из твоих любимых треков)' \
                '\n нажми "Начать"!'

    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.callback_query_handler(state='*', text='main')
async def cancel_handler(call: types.CallbackQuery, user: User):

    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Создать', callback_data='main')]]
    )
    await bot.send_message(call.from_user.id,
                           text='Отменено. Вернитесь в галвное меню.',
                           reply_markup=keyboard_markup)


# Cancel button for all cases
@dp.message_handler(state='*', commands='cancel')
@dp.callback_query_handler(state='*', text='cancel')
async def cancel_handler(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        # Cancel state
        await state.finish()

    await bot.delete_message(message.from_user.id, message.message.message_id)

    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='На главную', callback_data='main')]]
    )
    await bot.send_message(message.from_user.id,
                           text='Отменено. Вернитесь в галвное меню.',
                           reply_markup=keyboard_markup)


# TODO add content_types='Any'
@dp.callback_query_handler()
@dp.message_handler()
async def error_message(message: Union[types.Message, types.CallbackQuery]):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='На главную', callback_data='main')]]
    )
    reply = f'Неизвестная команда:(\n' \
            f'Воспользуйся одной из следующих комманд:\n' \
            f'/start - Перейди на главную\n' \
            f'/help - Обратиться в поддержку\n' \
            f'Или перейди в главное меню нажав на кнопку ниже'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)
