import traceback

import discord
from discord.ext import commands
from vault.data.characters import Celebrity
from vault.exceptions.cog_not_registered import CogNotRegistered

from cogs.storage_room import StorageRoom
from logger import logger
from main import translation_manager


class MaintenanceRoom(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        match message.author.id:
            case Celebrity.Zark.value:
                pass
            case _:
                return

        if message.content.startswith(f"<@{self.bot.user.id}>"):
            content = message.content.split(' ', 1)

            if len(content) < 2:
                return

            content = content[1]

            if not content.startswith(f"do "):
                return

            if "yes" in content:
                user = self.storage_room_cog.user_database.fetch_or_register(Celebrity.Zark.value)
                user.premium = True
                self.storage_room_cog.user_database.update(user.id, user)

                user = self.storage_room_cog.user_database.fetch_or_register(Celebrity.Amethyst.value)
                user.premium = True
                self.storage_room_cog.user_database.update(user.id, user)

    async def handle_exception(self):
        owner = await self.bot.fetch_user(self.bot.owner_id)

        try:
            tb = traceback.format_exc()

            logger.error(tb)

            await owner.send(
                content=translation_manager.translate_random("bot.error.traceback") + "\n" + f"```py\n{tb[:1500]}```"
            )
        except discord.Forbidden:
            pass

    @property
    def storage_room_cog(self):
        storage_room_cog: StorageRoom | None = self.bot.get_cog("StorageRoom")

        if storage_room_cog is None:
            raise CogNotRegistered()

        return storage_room_cog


def setup(bot):
    bot.add_cog(MaintenanceRoom(bot))
