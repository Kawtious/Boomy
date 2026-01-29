import asyncio
import os
from asyncio import CancelledError

import discord
from cogwatch import watch
from discord.ext import tasks
from vault.i18n.translation_manager import TranslationManager

from config import Config
from logger import logger

translation_manager = TranslationManager(os.path.join(Config.PROJECT_ROOT, "i18n", "locale"))
translation_manager.set_language("en-US")


class BoomyBot(discord.Bot):
    def __init__(self):
        super().__init__(
            intents=discord.Intents.default(),
            owner_id=Config.OWNER_ID
        )

        try:
            self.load_extension("cogs", recursive=True)
        except discord.ExtensionError:
            logger.error(f'Failed to load extensions')

    async def on_connect(self):
        await self.__waking_up()

        if self.auto_sync_commands:
            await self.sync_commands()

    @watch(
        path='cogs',
        preload=False,
        debug=False
    )
    async def on_ready(self):
        logger.info(translation_manager.translate("bot.ready", user=self.user))
        await self.__online()

        @tasks.loop(seconds=5 * 60)
        async def update_status():
            await self.__online()

        update_status.start()

    async def __online(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.custom,
                state=translation_manager.translate_random("bot.status.online")
            )
        )

    async def __waking_up(self):
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.custom,
                state=translation_manager.translate_random("bot.status.idle.waking_up")
            )
        )


async def main():
    bot = BoomyBot()

    try:
        await bot.start(Config.BOT_TOKEN)
    except CancelledError:
        await bot.close()
    except KeyboardInterrupt:
        await bot.close()


if __name__ == '__main__':
    asyncio.run(main())
