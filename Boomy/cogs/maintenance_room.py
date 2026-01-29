import traceback

import discord
from discord.ext import commands
from vault.data.characters import Celebrity

from logger import logger
from main import translation_manager


class MaintenanceRoom(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if message.author.bot:
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

            if "ratio" in message.content:
                ratio = "https://tenor.com/view/zorua-zorua-skill-issue-stay-mad-zorua-stay-mad-zorua-reaction-gif-3559579621891501142"
                # user = await self.bot.fetch_user(Celebrity.Amethyst.value)
                # await user.send(ratio)
                await message.reply(ratio)

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


def setup(bot):
    bot.add_cog(MaintenanceRoom(bot))
