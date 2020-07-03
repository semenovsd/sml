"""Аутентификация пользователей — проверяем есть ли пользователь с таким телеграмм ID в бд"""
from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware

from database import User


class AccessMiddleware(BaseMiddleware):

    def __init__(self):
        self.user = User()
        super().__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict):
        data['user'] = await self.user.get(message.from_user.id)  # types.User.get_current().id

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        data['user'] = await self.user.get(callback_query.from_user.id)
