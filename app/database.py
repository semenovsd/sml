from gino import Gino
from gino.schema import GinoSchemaVisitor
from sqlalchemy import (BigInteger, Column, Integer,
                        Sequence, String, sql, ForeignKey)
from sqlalchemy.dialects import postgresql

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

    async def get(self, user_id: int):
        user = await User.query.where(User.user_id == user_id).gino.first()
        if user:
            return user
        self.user_id = user_id
        await self.create()
        return self

    async def get_albums(self):
        return await Album.query.where(Album.user_id == self.user_id).gino.all()


class Album(db.Model):
    __tablename__ = 'albums'
    query: sql.Select

    # TODO убрать последовательность так как будут удаляться
    id = Column(Integer, Sequence('album_id_seq'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    name = Column(String(50), default=None)
    tracks = Column(postgresql.ARRAY(String(80)), default=[])

    async def new(self, name, user_id):
        self.user_id = int(user_id)
        self.name = name
        self.tracks = []
        await self.create()
        return self

    async def get(self, album_id):
        album = await Album.query.where(Album.id == int(album_id)).gino.first()
        # self.id = album.id
        # self.user_id = album.user_id
        # self.name = album.name
        # self.tracks = album.tracks
        return album

    async def get_tracks(self):
        return self.tracks

    async def set_tracks(self, tracks):
        await self.update(tracks=tracks).apply()


async def create_db():
    await db.set_bind(f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{PG_HOST}/{POSTGRES_DB}')

    # Create tables
    db.gino: GinoSchemaVisitor
    # await db.gino.drop_all()  # Drop the db
    await db.gino.create_all()
