from aiogram.dispatcher.handler import ctx_data

from database import User


def is_subscriber(handlers) -> bool:
    data = ctx_data.get()
    user: User = data['user']
    return user.subscribe if hasattr(user, 'subscribe') else False


def is_not_subscriber(handlers) -> bool:
    data = ctx_data.get()
    user: User = data['user']
    return True if hasattr(user, 'subscribe') and user.subscribe is False else False
