import discord
from discord.ext import commands
from fastapi import status, APIRouter
from fastapi.responses import JSONResponse
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.console_not_valid import ConsoleNotValid
from vault.exceptions.game_already_registered import GameAlreadyRegistered
from vault.exceptions.invalid_rom import InvalidROM

from cogs.storage_room import StorageRoom
from main import translation_manager


class DeskAPI(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.router = APIRouter()
        self.router.add_api_route(
            "/desk/check-in",
            self.checkin,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )

    async def checkin(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                if error is not None:
                    match error:
                        case "InvalidROM":
                            raise InvalidROM()
                        case "GameAlreadyRegistered":
                            raise GameAlreadyRegistered()
                        case "ConsoleNotValid":
                            raise ConsoleNotValid()
                        case _:
                            raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.desk.checkin.success",
                        lang=locale
                    )
                )
            except InvalidROM:
                await self.reply_error(response, "response.desk.checkin.fail_invalid_cartridge", locale)
            except GameAlreadyRegistered:
                await self.reply_error(response, "response.desk.checkin.fail_already_checked_in", locale)
            except ConsoleNotValid:
                await self.reply_error(response, "response.desk.checkin.fail_invalid_console", locale)
            except Exception:
                await self.reply_error(response, "response.desk.checkin.fail_unknown", locale)
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
    bot.add_cog(DeskAPI(bot))
