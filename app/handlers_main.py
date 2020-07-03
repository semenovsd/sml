import logging
from asyncio import sleep
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import exceptions

from database import User, Album
from load_all import bot, dp

from states import EditAlbum


@dp.message_handler(CommandStart())
async def start_cmd_handler(message: types.Message):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Начать', callback_data='main')]]
    )
    reply = 'Привет! Я помогу тебе собрать плейлисты из твоих любимых треков)' \
            '\n нажми "Начать"!'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.callback_query_handler(text='main')
async def cancel_handler(call: types.CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Создать', callback_data='new_album')],
        ]
    )
    user_albums = await user.get_albums()
    if user_albums:
        keyboard_markup.add(InlineKeyboardButton(text='Слушать', callback_data='show_album'))
        keyboard_markup.add(InlineKeyboardButton(text='Поделиться', callback_data='share_album'))
    await bot.send_message(call.from_user.id,
                           text='Создавай плейлисты своей любимой музыки, слушай и делись с другими!',
                           reply_markup=keyboard_markup)


# MAKE ALBUM
@dp.callback_query_handler(text='new_album')
async def new_album(call: types.CallbackQuery):
    await EditAlbum.EditName.set()
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
        ]
    )
    reply = 'Как назвать альбом? (до 50 символов)'
    await bot.send_message(
        chat_id=call.from_user.id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.message_handler(state=EditAlbum.EditName)
async def edit_phone_number(message: types.Message, user: User, state: FSMContext):
    if len(message.text) < 50:
        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='На главную', callback_data='main')],
            ]
        )
        await state.finish()
        album = await Album().new(name=message.text, user_id=user.user_id)
        reply = f'Создан альбом - {album.name}! Перешли мне аудио трэки, чтобы добавить их в новый альбом.'
    else:
        keyboard_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Отмена', callback_data='cancel')],
            ]
        )
        reply = 'Слишком длинное название, введи ещё раз.'
    await bot.send_message(
        chat_id=message.from_user.id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(text='show_album')
async def show_album(call: types.CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='На главную', callback_data='main')],
        ]
    )
    albums = await user.get_albums()
    if albums:
        for album in albums:
            keyboard_markup.add(
                InlineKeyboardButton(text=album.name, callback_data=f'play_album:{album.id}')
            )
        reply = 'Какой альбом открыть?'
    else:
        reply = 'У тебя ещё нет альбомов. Создать новый?'
        keyboard_markup.add(
            InlineKeyboardButton(text='Создать', callback_data='new_album')
        )
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(text='share_album')
async def share_album(call: types.CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='На главную', callback_data='main')],
        ]
    )
    albums = await user.get_albums()
    if albums:
        bot_username = (await bot.me).username
        for album in user.albums:
            keyboard_markup.add(
                InlineKeyboardButton(text=album.album_name, url=f'https://t.me/{bot_username}?start={album.id}')
            )
        reply = 'Поделись ссылкой на один из своих альбомов'
    else:
        reply = 'У тебя ещё нет альбомов. Создать новый?'
        keyboard_markup.add(
            InlineKeyboardButton(text='Создать', callback_data='new_album')
        )
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=call.message.message_id,
        text=reply,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(text_contains='play_album')
async def play_album(call: types.CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='На главную', callback_data='main')],
        ]
    )
    album_id = call.data.split(':')
    album_id = album_id[-1] if len(album_id) > 1 else None
    album = await Album().get(album_id=album_id) if album_id else None

    if album and album.tracks:
        reply = 'Приятного прослушивания!'
        log = logging.getLogger('play_album')
        for track in album.tracks:
            try:
                await bot.send_audio(call.from_user.id, audio=track)
                await sleep(0.1)  # Telegram limit 30 message per second, here set 10 msg per second

            except exceptions.RetryAfter as e:
                await sleep(e.timeout)
                return await bot.send_audio(call.from_user.id, audio=track)

            except exceptions.TelegramAPIError:
                log.exception(f'Target [ID:{call.from_user.id}]: failed')
                pass

            except exceptions:
                log.exception(f'Target [ID:{call.from_user.id}]: failed')

            else:
                log.info(f'Target [ID:{call.from_user.id}]: success')

    else:
        reply = 'В этом альбом ещё нет трэков. Что бы добавить просто перешли их мне.'
    await bot.send_message(call.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.message_handler(content_types=types.ContentType.AUDIO)
async def add_music(message: types.Message):
    await bot.delete_message(message.from_user.id, message.message_id)
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='+', callback_data='add_track'),
                InlineKeyboardButton(text='-', callback_data='del_track')
            ]
        ]
    )
    await bot.send_audio(message.from_user.id, audio=message.audio.file_id, reply_markup=keyboard_markup)


@dp.callback_query_handler(text_contains='add_track')
async def add_track(call: types.CallbackQuery, user: User):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Создать новый альбом', callback_data=f'new_album')]]
    )

    track_file_id = call.message.audio.file_id
    user_albums = await user.get_albums()
    if user_albums:
        # получаем id альбома
        album_id = call.data.split(':')
        album_id = album_id[-1] if len(album_id) > 1 else None
        if album_id:
            album = await Album().get(album_id=album_id)
            if track_file_id in album.tracks:
                album.tracks.remove(track_file_id)
            else:
                album.tracks.append(track_file_id)

        for album in user_albums:
            if track_file_id in album.tracks:
                keyboard_markup.add(
                    InlineKeyboardButton(text=f'++ {album.name}', callback_data=f'add_track:{album.id}')
                )
            else:
                keyboard_markup.add(
                    InlineKeyboardButton(text=f'-- {album.name}', callback_data=f'add_track:{album.id}')
                )

    await bot.edit_message_reply_markup(
        inline_message_id=call.message.message_id,
        reply_markup=keyboard_markup
    )


@dp.callback_query_handler(text='del_track')
async def del_track(call: types.CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)


# Cancel button for all cases
@dp.message_handler(state='*', commands='cancel')
@dp.callback_query_handler(state='*', text='cancel')
async def cancel_handler(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    await bot.delete_message(message.from_user.id, message.message.message_id)

    current_state = await state.get_state()
    if current_state:
        await state.finish()

    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='На главную', callback_data='main')]]
    )
    await bot.send_message(message.from_user.id,
                           text='Отменено. Вернитесь в галвное меню.',
                           reply_markup=keyboard_markup)


# TODO add content_types='Any' exception content_types=types.ContentType.AUDIO
@dp.callback_query_handler()
@dp.message_handler()
async def error_message(message: Union[types.Message, types.CallbackQuery]):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='На главную', callback_data='main')]]
    )
    reply = f'Неизвестная команда:(\n' \
            f'Или перейди в главное меню нажав на кнопку ниже'
    await bot.send_message(message.from_user.id, text=reply, reply_markup=keyboard_markup)
