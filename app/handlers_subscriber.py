import re

from aiogram.dispatcher import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)

from database import User
from filters import is_subscriber
from load_all import bot, dp
from states import EditWithdraw


@dp.callback_query_handler(is_subscriber, text='main')
async def main(call: CallbackQuery):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Твои плейлисты', callback_data='user_playlists')],
            [InlineKeyboardButton(text='Создать новый', callback_data='new_list')],
        ]
    )
    reply = 'Создать новый плейлист или показать сохранённые?'
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(is_subscriber, text='user_playlists')
async def user_playlists(call: CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отправить приглашение', callback_data='send_invite')],
            [InlineKeyboardButton(text='Вывод денег', callback_data='withdraw')],
        ]
    )
    reply = 'Какой плейлист показать (введи его номер, например 1)?'
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(is_subscriber, text='new_list')
async def send_invite(call: CallbackQuery, user: User):
    bot_username = (await bot.me).username
    ref_link = f'https://t.me/{bot_username}?start={user.user_id}'
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=ref_link
    )
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='user_account')],
        ]
    )
    reply = f'Твоя ссылка-приглашение выше \U0001F446. Используй её для приглашения новый участников!'
    await bot.send_message(call.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.callback_query_handler(is_subscriber, text='withdraw_data')
async def withdraw_data(call: CallbackQuery, user: User):
    data = await user.get_personal_info('full_name', 'phone_number', 'email', 'passport_number')

    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Редактировать данные', callback_data='edit_withdraw')],
            [InlineKeyboardButton(text='Назад', callback_data='user_account')],
        ]
    )

    if data:
        reply = f'Твои данные для вывода денег, они могут отличаться от твоих данных в телеграмме, но должны ' \
                f'полностью совпадать с данными владельца карты или телефона на который выводяться деньги:\n' \
                f'ФИО: {data["full_name"]}\n' \
                f'Номер телефона: {data["phone_number"]}\n' \
                f'Email: {data["email"]}\n' \
                f'Номер паспорта: {data["passport_number"]}\n'
    else:
        reply = 'Твои данные для вывода незаполнены! Нажми Редактировать данные для заполнения!'

    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(is_subscriber, text='withdraw')
async def withdraw(call: CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Данны для вывода денег', callback_data='withdraw_data')],
            [InlineKeyboardButton(text='Назад', callback_data='user_account')],
            [InlineKeyboardButton(text='Вывести деньги', callback_data='make_withdraw')]
        ]
    )
    reply = f'Сейчас у Вас на балансе: {user.balance // 100},00 рублей.\n' \
            f'Минимальная сумма вывода - 1000,00 рублей\n' \
            f'Учтите, что в зависимости от способа вывода денег взымается комиссия платёжной системы.\n' \
            f'Подробнее с тарифами можно ознакомиться здесь:\n' \
            f'Яндекс.касса: url\n' \
            f'Tenzzo: url' \
            f'Так же для некоторых способов вывода денег в соответствии с' \
            f' действующим законодательством необходимо заполнить персональные данные'
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


# EDIT PERSONAL_DATA
@dp.callback_query_handler(is_subscriber, text='edit_withdraw', state='*')
async def edit_withdraw(call: CallbackQuery):
    await EditWithdraw.EditFullName.set()
    reply = 'Введите ФИО на русском в формате: Фамилия Имя Отчество\n' \
            '(не более 50 символов и только латинские буквы)'
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )
    await bot.send_message(call.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.message_handler(is_subscriber, state=EditWithdraw.EditFullName)
async def edit_phone_number(message: Message, state: FSMContext):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )
    if len(message.text) < 50:
        await state.update_data(full_name=message.text.capitalize())
        await EditWithdraw.EditPhoneNumber.set()
        reply = 'Введите ваш номер телефона в формате 79219876543, без знака + и пробелов, только цифры'
    else:
        reply = 'Вы неправильно ввели своё ФИО, ограничение 50 символов включая пробелы, введите ещё раз'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.message_handler(is_subscriber, state=EditWithdraw.EditPhoneNumber)
async def edit_email(message: Message, state: FSMContext):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )
    if len(message.text) == 11 and re.fullmatch(r'^7\d{10}', message.text):
        await state.update_data(phone_number=message.text)
        await EditWithdraw.EditEmail.set()
        reply = 'Введите ваш email, до 50 символов'
    else:
        reply = 'Вы неправильно ввели своё номер телефона, ограничение 11 чисел начиная с 7, введите ещё раз:'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.message_handler(is_subscriber, state=EditWithdraw.EditEmail)
async def edit_passport_number(message: Message, state: FSMContext):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )
    if len(message.text) < 50 and re.fullmatch(r'(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)',
                                               message.text.lower()):
        await state.update_data(email=message.text)
        await EditWithdraw.EditPassportNumber.set()
        reply = 'Введите серию и номер вашего паспорта в формате xxxxxxxxxx, без пробелов и только цифры'
    else:
        reply = 'Вы неправильно ввели свой email, ограничение 50 символов, введите ещё раз:'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.message_handler(is_subscriber, state=EditWithdraw.EditPassportNumber)
async def edit_withdraw_check(message: Message, state: FSMContext):
    if len(message.text) == 10 and message.text.isnumeric():
        await state.update_data(passport_number=message.text)
        await EditWithdraw.EditCheck.set()
        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Подтвердить', callback_data='approve_edit_withdraw')],
                [InlineKeyboardButton(text='Редактировать', callback_data='edit_withdraw')],
                [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
            ]
        )
        data = await state.get_data()
        reply = 'Проверьте данные:\n' \
                f'ФИО: {data["full_name"]}\n' \
                f'Номер телефона: {data["phone_number"]}\n' \
                f'Почта: {data["email"]}\n' \
                f'Номер паспорта: {data["passport_number"]}\n' \
                f'Если всё правильно нажмите Подтвердить.' \
                'Или нажмите Редактировать для повторного ввода'
        await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)
    else:
        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
            ]
        )
        reply = 'Вы неправильно ввели номер паспорта, должно быть 10 цифр, введите ещё раз:'
        await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.callback_query_handler(is_subscriber, text='approve_edit_withdraw', state=EditWithdraw.EditCheck)
async def approve_edit_withdraw(call: CallbackQuery, user: User, state: FSMContext):
    async with state.proxy() as data:
        await user.save_personal_info(data, 'full_name', 'phone_number', 'email', 'passport_number')
    await state.finish()
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Перейти в аккаунт', callback_data='user_account')],
        ]
    )
    reply = 'Теперь Вам доступны все виды вывода денег, а ваши данные будут храниться в надёжном месте!'
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )
