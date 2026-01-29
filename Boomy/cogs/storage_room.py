import discord
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vault.data.database.cartridge import Cartridge
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.gameboy_profile import GameBoyProfile
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.pokemon import Pokemon
from vault.data.database.statistics import Statistics
from vault.data.database.user import User
from vault.database.cartridge_database import CartridgeDatabase
from vault.database.user_database import UserDatabase

from config import Config


class StorageRoom(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.__session = None
        self.__user_database = None
        self.__cartridge_database = None

    async def cog_load(self):
        engine = create_engine(Config.DATABASE_CONNECTION, echo=False)

        User.metadata.create_all(engine)
        Statistics.metadata.create_all(engine)
        Pokemon.metadata.create_all(engine)
        GameBoyProfile.metadata.create_all(engine)
        Cartridge.metadata.create_all(engine)
        GameBoyCartridge.metadata.create_all(engine)
        NESCartridge.metadata.create_all(engine)

        self.__session = Session(engine)
        self.__user_database = UserDatabase(self.__session)
        self.__cartridge_database = CartridgeDatabase(self.__session)

    async def cog_unload(self):
        if self.__session:
            self.__session.close()
            self.__session = None

            self.__user_database = None
            self.__cartridge_database = None

    @property
    def user_database(self) -> UserDatabase:
        return self.__user_database

    @property
    def cartridge_database(self) -> CartridgeDatabase:
        return self.__cartridge_database


__storage_room_cog: StorageRoom | None = None


def setup(bot):
    global __storage_room_cog

    __storage_room_cog = StorageRoom(bot)
    bot.add_cog(__storage_room_cog)

    bot.loop.create_task(__storage_room_cog.cog_load())


def teardown(bot):
    global __storage_room_cog

    if not __storage_room_cog:
        return

    bot.loop.create_task(__storage_room_cog.cog_unload())
    __storage_room_cog = None
