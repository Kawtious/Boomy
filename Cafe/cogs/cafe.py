import asyncio
import time
from typing import Any

import aiohttp
import discord
from discord.ext import commands
from vault.exceptions.cog_not_registered import CogNotRegistered

from cogs.maintenance_room import MaintenanceRoom
from config import Config
from main import translation_manager


class Cafe(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(
        name="ping"
    )
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "ping_time": time.time()
        }

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.cafe.ping.success", lang=ctx.interaction.locale
            )
        )

        data["response_id"] = response.id

        await response.edit(
            content=translation_manager.translate_random(
                "response.cafe.ping.success_ms",
                lang=ctx.interaction.locale,
                ms=round((time.time() - data["ping_time"]) * 1000, 4)
            )
        )

        async def ping_them_creatures(url, sesh):
            try:
                await sesh.post(url, json=data)
            except Exception:
                pass

        creatures = [
            f"{Config.CAFE_API}/ping",
            f"{Config.BOOMY_API}/ping",
            f"{Config.BERRY_API}/ping",
            f"{Config.JAX_API}/ping",
        ]

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(ping_them_creatures(url, session) for url in creatures))

    @ping.error
    async def on_ping_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        response = await self.respond_error(
            interaction=ctx.interaction,
            message="response.cafe.ping.fail_unknown",
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        async def ping_them_creatures(url, sesh: aiohttp.ClientSession):
            try:
                await sesh.post(url, json=data)
            except Exception:
                pass

        creatures = [
            f"{Config.CAFE_API}/ping",
            f"{Config.BOOMY_API}/ping",
            f"{Config.BERRY_API}/ping",
            f"{Config.JAX_API}/ping",
        ]

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(ping_them_creatures(url, session) for url in creatures))

    @property
    def maintenance_room_cog(self):
        maintenance_room_cog: MaintenanceRoom | None = self.bot.get_cog("MaintenanceRoom")

        if maintenance_room_cog is None:
            raise CogNotRegistered()

        return maintenance_room_cog


def setup(bot):
    bot.add_cog(Cafe(bot))
