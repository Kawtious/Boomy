import asyncio
import os
import shutil
from asyncio import CancelledError

import discord
from cogwatch import watch
from discord.ext import tasks
from vault.i18n.translation_manager import TranslationManager

from config import Config
from logger import logger

translation_manager = TranslationManager(os.path.join(Config.PROJECT_ROOT, "i18n", "locale"))
translation_manager.set_language("en-US")


class CafeBot(discord.Bot):
    def __init__(self):
        super().__init__(
            intents=discord.Intents.default(),
            owner_id=Config.OWNER_ID,
        )

        self.load_extension("cogs", recursive=True)

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


def clear_temp_folder():
    tmp_folder = os.path.join(Config.PROJECT_ROOT, "temp")

    for filename in os.listdir(tmp_folder):
        file_path = os.path.join(tmp_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error('Failed to delete %s. Reason: %s' % (file_path, e))


async def main():
    clear_temp_folder()
    bot = CafeBot()

    try:
        await bot.start(Config.BOT_TOKEN)
    except CancelledError:
        await bot.close()
    except KeyboardInterrupt:
        await bot.close()


if __name__ == '__main__':
    asyncio.run(main())
