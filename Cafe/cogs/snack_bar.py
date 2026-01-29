import discord
from discord.ext import commands


class SnackBar(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    snacks = discord.SlashCommandGroup(
        name="snacks"
    )

    async def menu(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        raise NotImplemented()


def setup(bot):
    bot.add_cog(SnackBar(bot))
