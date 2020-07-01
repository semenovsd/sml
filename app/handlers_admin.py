import logging
from asyncio import sleep
from typing import Union

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import exceptions

from config import TG_ADMINS_ID
from database import Statistic
from load_all import bot, dp
from states import Mailing


@dp.message_handler(user_id=TG_ADMINS_ID, commands='admin')
@dp.callback_query_handler(user_id=TG_ADMINS_ID, text='admin')
async def admin_panel(message: Union[types.Message, types.CallbackQuery]):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Посмотреть пользователей', callback_data='check_users_stat')],
            [InlineKeyboardButton(text='Перейти в аккаунт', callback_data='user_account')],
            [InlineKeyboardButton(text='Сделать рассылку', callback_data='tell_everyone')],
        ]
    )
    statistics = Statistic()
    reply = 'Сейчас в системе:\n' \
            f'Пользователей: {await statistics.get_users_count()}\n' \
            f'Подписчиков: {await statistics.get_subscribers_count()}\n' \
            f'Получено оплат: {await statistics.get_users_payments_amount()} руб.\n' \
            f'На балансе пользователей: {await statistics.get_users_balances_amount()} руб.\n' \
            'Что бы узнать подробную статистику по пользователем, перейди в раздел -' \
            'Посмотреть пользователей'
    await bot.send_message(chat_id=message.from_user.id, text=reply, reply_markup=keyboard_markup)


@dp.callback_query_handler(user_id=TG_ADMINS_ID, text='check_users_stat')
async def check_users_stat(call: types.CallbackQuery):
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='admin')],
        ]
    )
    data = Statistic()
    reply = f'{await data.get_users_statistic()}'
    await bot.send_message(call.from_user.id, text=reply, reply_markup=keyboard_markup)


# Cancel button for all cases
@dp.message_handler(state='*', commands='admin_cancel')
@dp.callback_query_handler(state='*', text='admin_cancel')
async def cancel_handler(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        # Cancel state
        await state.finish()

    await bot.delete_message(message.from_user.id, message.message.message_id)

    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Меню админа', callback_data='admin')]]
    )
    await bot.send_message(message.from_user.id,
                           text='Отменено. Вернитесь в админское меню.',
                           reply_markup=keyboard_markup)


# Send message to all users
@dp.callback_query_handler(user_id=TG_ADMINS_ID, text='tell_everyone')
async def mailing(call: types.CallbackQuery):
    await bot.send_message(call.from_user.id, text='Пришлите текст рассылки')
    await Mailing.Text.set()


@dp.message_handler(user_id=TG_ADMINS_ID, state=Mailing.Text)
async def mailing(message: types.Message, state: FSMContext):
    text = message.text
    await state.update_data(mailing_text=text)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Отправить сообщение', callback_data='mailing_start')],
            [InlineKeyboardButton(text='Отмена', callback_data='admin_cancel')],
        ]
    )
    await message.answer(f'Тексты сообщения:\n{message.text}\n Введите повторно текст для редактирования',
                         reply_markup=markup)


@dp.callback_query_handler(user_id=TG_ADMINS_ID, text='mailing_start', state=Mailing.Text)
async def mailing_start(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mailing_text = 'Сообщение от администратора:\n' + data.get('mailing_text')
    await state.finish()
    await call.message.edit_reply_markup()
    log = logging.getLogger('broadcast')
    users_id = Statistic()
    for user_id in (await users_id.get_users_id()):
        try:
            await bot.send_message(user_id, mailing_text)
            await sleep(0.05)  # Telegram limit 30 message per second, here set 20 msg per second

        except exceptions.BotBlocked:
            log.error(f"Target [ID:{user_id}]: blocked by user")

        except exceptions.ChatNotFound:
            log.error(f"Target [ID:{user_id}]: invalid user ID")

        except exceptions.RetryAfter as e:
            log.error(f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.")
            await sleep(e.timeout)
            # TODO This is not real recursive call
            return await bot.send_message(user_id, mailing_text)  # Recursive call

        except exceptions.UserDeactivated:
            log.error(f"Target [ID:{user_id}]: user is deactivated")

        except exceptions.TelegramAPIError:
            log.exception(f"Target [ID:{user_id}]: failed")
            pass

        else:
            log.info(f"Target [ID:{user_id}]: success")
    keyboard_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Назад', callback_data='admin')],
        ]
    )
    await call.message.answer("Рассылка выполнена.", reply_markup=keyboard_markup)
