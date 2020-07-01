import json

from gino import Gino
from gino.schema import GinoSchemaVisitor
from sqlalchemy import (BigInteger, Column, Integer,
                        Sequence, String, sql, ForeignKey)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSON

from config import PG_HOST, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER

import logging

log = logging.getLogger('broadcast')

db = Gino()


# Документация
# http://gino.fantix.pro/en/latest/tutorials/tutorial.html
class User(db.Model):
    __tablename__ = 'users'
    query: sql.Select

    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    user_id = Column(BigInteger, unique=True)

    async def get_or_create(self, user_id: int):
        user = await User.query.where(User.user_id == user_id).gino.first()
        # If user exist return user
        if user:
            return user
        self.user_id = user_id
        await self.create()
        return self


class MusicList(db.Model):
    __tablename__ = 'musiclists'
    query: sql.Select

    id = Column(Integer, Sequence('ml_id_seq'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    list_name = Column(String(50), default=None)
    music_list = Column(JSON(1024))

    async def create(self, user_id, music_list):
        self.user_id = int(user_id)
        self.list_name = str(music_list.list_name)
        self.music_list = json.loads(music_list.list)
        await self.create()

    async def get(self, *args):
        return {data: json.loads(self.music_list).get(data) for data in args} if self.music_list else None

    async def set(self, data, *args):
        if self.music_list:
            saving_info = json.loads(self.music_list)
            saving_info.update({arg: data[arg] for arg in data if arg in args})
            await self.update(Musiclist.music_list=json.dumps(saving_info)).apply()
        else:
            await self.update(MusicList.music_list=json.dumps({arg: data[arg] for arg in data if arg in args})).apply()


async def create_db():
    await db.set_bind(f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{PG_HOST}/{POSTGRES_DB}')

    # Create tables
    db.gino: GinoSchemaVisitor
    # await db.gino.drop_all()  # Drop the db
    await db.gino.create_all()
