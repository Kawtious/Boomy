import discord
import uvicorn
from discord.ext import commands
from fastapi import FastAPI
from vault.exceptions.cog_not_registered import CogNotRegistered

from cogs.api.cafe_api import CafeAPI


class WiFi(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.__server: uvicorn.Server | None = None

    async def load(self):
        api = FastAPI()

        api.include_router(self.cafe_api_cog.router)

        api_version = 1

        config = uvicorn.Config(api, port=8000, root_path=f"/cafe/api/v{api_version}", loop="asyncio", lifespan="on")
        self.__server = uvicorn.Server(config)

        await self.__server.serve()

    async def unload(self):
        if self.__server:
            await self.__server.shutdown()
            self.__server = None

    @property
    def cafe_api_cog(self):
        cafe_api_cog: CafeAPI | None = self.bot.get_cog("CafeAPI")

        if cafe_api_cog is None:
            raise CogNotRegistered()

        return cafe_api_cog


__wifi_cog: WiFi | None = None


def setup(bot):
    global __wifi_cog

    __wifi_cog = WiFi(bot)
    bot.add_cog(__wifi_cog)

    bot.loop.create_task(__wifi_cog.load())


def teardown(bot):
    global __wifi_cog

    if not __wifi_cog:
        return

    bot.loop.create_task(__wifi_cog.unload())
    __wifi_cog = None
