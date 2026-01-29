import discord
import uvicorn
from discord.ext import commands
from fastapi import FastAPI
from vault.exceptions.cog_not_registered import CogNotRegistered

from cogs.api.boomy_api import BoomyAPI
from cogs.api.desk_api import DeskAPI
from cogs.api.gaming_room_api import GamingRoomAPI
from cogs.api.stadium_api import StadiumAPI


class Smartphone(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.__server: uvicorn.Server | None = None

    async def cog_load(self):
        api = FastAPI()

        api.include_router(self.boomy_api_cog.router)
        api.include_router(self.desk_api_cog.router)
        api.include_router(self.gaming_room_api_cog.router)
        api.include_router(self.stadium_api_cog.router)

        api_version = 1

        config = uvicorn.Config(api, port=8001, root_path=f"/boomy/api/v{api_version}", loop="asyncio", lifespan="on")
        self.__server = uvicorn.Server(config)

        await self.__server.serve()

    async def cog_unload(self):
        if self.__server:
            await self.__server.shutdown()
            self.__server = None

    @property
    def boomy_api_cog(self):
        boomy_api_cog: BoomyAPI | None = self.bot.get_cog("BoomyAPI")

        if boomy_api_cog is None:
            raise CogNotRegistered()

        return boomy_api_cog

    @property
    def desk_api_cog(self):
        desk_api_cog: DeskAPI | None = self.bot.get_cog("DeskAPI")

        if desk_api_cog is None:
            raise CogNotRegistered()

        return desk_api_cog

    @property
    def gaming_room_api_cog(self):
        gaming_room_api_cog: GamingRoomAPI | None = self.bot.get_cog("GamingRoomAPI")

        if gaming_room_api_cog is None:
            raise CogNotRegistered()

        return gaming_room_api_cog

    @property
    def stadium_api_cog(self):
        stadium_api_cog: StadiumAPI | None = self.bot.get_cog("StadiumAPI")

        if stadium_api_cog is None:
            raise CogNotRegistered()

        return stadium_api_cog


__smartphone_cog: Smartphone | None = None


def setup(bot):
    global __smartphone_cog

    __smartphone_cog = Smartphone(bot)
    bot.add_cog(__smartphone_cog)

    bot.loop.create_task(__smartphone_cog.cog_load())


def teardown(bot):
    global __smartphone_cog

    if not __smartphone_cog:
        return

    bot.loop.create_task(__smartphone_cog.cog_unload())
    __smartphone_cog = None
