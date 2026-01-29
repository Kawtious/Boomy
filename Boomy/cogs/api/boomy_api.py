import time

import discord
from discord.ext import commands
from fastapi import status, APIRouter
from fastapi.responses import JSONResponse
from vault.exceptions.cog_not_registered import CogNotRegistered

from cogs.storage_room import StorageRoom
from main import translation_manager


class BoomyAPI(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.router = APIRouter()
        self.router.add_api_route(
            "/ping",
            self.ping,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )

    async def ping(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)
        ping_time: int | None = data.get("ping_time", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                reply = await response.reply(
                    content=translation_manager.translate_random(
                        "response.api.boomy.ping.success", lang=locale
                    )
                )

                await reply.edit(
                    content=translation_manager.translate_random(
                        "response.api.boomy.ping.success_ms",
                        lang=locale,
                        ms=round((time.time() - ping_time) * 1000, 4)
                    )
                )
            except Exception:
                await self.reply_error(response, "response.api.boomy.ping.fail_unknown", locale)
        except discord.InvalidData:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "discord.InvalidData"}
            )
        except discord.InvalidArgument:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "discord.InvalidArgument"}
            )
        except discord.NotFound:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "discord.NotFound"}
            )
        except discord.Forbidden:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "discord.Forbidden"}
            )
        except discord.HTTPException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "discord.HTTPException"}
            )
        except discord.DiscordException:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "discord.DiscordException"}
            )

        return None

    @staticmethod
    async def reply_error(response: discord.Message, message: str, lang, prefix="", suffix="", **kwargs):
        content = prefix
        content += translation_manager.translate_random(message, lang=lang, **kwargs)
        content += "\n"
        content += "-# "
        content += translation_manager.translate(f'{message}.error', lang=lang, **kwargs)
        content += suffix

        return await response.reply(content=content, **kwargs)

    @property
    def storage_room_cog(self):
        storage_room_cog: StorageRoom | None = self.bot.get_cog("StorageRoom")

        if storage_room_cog is None:
            raise CogNotRegistered()

        return storage_room_cog


def setup(bot):
    bot.add_cog(BoomyAPI(bot))
