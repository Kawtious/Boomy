import discord
from discord import DMChannel
from discord.ext import commands
from fastapi import status, APIRouter
from fastapi.responses import JSONResponse
from vault.exceptions.boomy_refuses_invite import BoomyRefusesInvite
from vault.exceptions.cafe_refuses_invite import CafeRefusesInvite
from vault.exceptions.cartridge_not_found import GameNotStarted
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.console_not_valid import ConsoleNotValid
from vault.exceptions.game_does_not_exist import GameDoesNotExist
from vault.exceptions.invalid_frame_data import InvalidFrameData
from vault.exceptions.last_message_not_found import LastMessageNotFound
from vault.exceptions.no_previous_state import NoPreviousState
from vault.exceptions.no_save_state import NoSaveState
from vault.exceptions.not_enough_joypads import NotEnoughJoypads
from vault.exceptions.unauthorized_joypad_access import UnauthorizedJoypadAccess
from vault.exceptions.user_already_invited import UserAlreadyInvited
from vault.exceptions.user_is_cartridge_owner import UserIsCartridgeOwner

from cogs.storage_room import StorageRoom
from main import translation_manager


class GamingRoomAPI(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.router = APIRouter()
        self.router.add_api_route(
            "/gaming-room/play",
            self.play,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/invite",
            self.invite,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/restart",
            self.restart,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/save",
            self.save,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/load",
            self.load,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/rewind",
            self.rewind,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/gaming-room/joypad",
            self.joypad,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )

    async def play(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "GameDoesNotExist":
                        raise GameDoesNotExist()
                    case "InvalidFrameData":
                        raise InvalidFrameData()
                    case "ConsoleNotValid":
                        raise ConsoleNotValid()
                    case _:
                        raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.gaming_room.play.success",
                        lang=locale
                    )
                )
            except GameDoesNotExist:
                await self.reply_error(response, "response.gaming_room.play.fail_not_found", locale)
            except InvalidFrameData:
                await self.reply_error(response, "response.gaming_room.play.fail_console_broke", locale)
            except ConsoleNotValid:
                await self.reply_error(response, "response.gaming_room.play.fail_invalid_console", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.play.fail_unknown", locale)
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

    async def invite(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "CafeRefusesInvite":
                        raise CafeRefusesInvite()
                    case "BoomyRefusesInvite":
                        raise BoomyRefusesInvite()
                    case "GameNotStarted":
                        raise GameNotStarted()
                    case "NotEnoughJoypads":
                        raise NotEnoughJoypads()
                    case "UserIsCartridgeOwner":
                        raise UserIsCartridgeOwner()
                    case "UserAlreadyInvited":
                        raise UserAlreadyInvited()
                    case "LastMessageNotFound":
                        raise LastMessageNotFound()
                    case _:
                        raise Exception()

                try:
                    await response.reply(
                        content=translation_manager.translate_random(
                            "response.gaming_room.invite.success", lang=locale
                        )
                    )
                except discord.DiscordException:
                    return JSONResponse(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        content={"error": "discord.DiscordException"}
                    )
            except BoomyRefusesInvite:
                await self.reply_error(response, "response.gaming_room.invite.fail_boomy_refuses", locale)
            except GameNotStarted:
                await self.reply_error(response, "response.gaming_room.invite.fail_no_game", locale)
            except NotEnoughJoypads:
                await self.reply_error(response, "response.gaming_room.invite.fail_not_enough_joypads", locale)
            except UserIsCartridgeOwner:
                await self.reply_error(response, "response.gaming_room.invite.fail_invited_self", locale)
            except UserAlreadyInvited:
                await self.reply_error(response, "response.gaming_room.invite.fail_already_invited", locale)
            except LastMessageNotFound:
                await self.reply_error(response, "response.gaming_room.invite.fail_msg_not_found", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.invite.fail_unknown", locale)
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

    async def restart(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "GameNotStarted":
                        raise GameNotStarted()
                    case _:
                        raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.gaming_room.restart.success",
                        lang=locale
                    )
                )
            except GameNotStarted:
                await self.reply_error(response, "response.gaming_room.restart.fail_no_game", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.restart.fail_unknown", locale)
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

    async def save(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "GameNotStarted":
                        raise GameNotStarted()
                    case _:
                        raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.gaming_room.save.success",
                        lang=locale
                    )
                )
            except GameNotStarted:
                await self.reply_error(response, "response.gaming_room.save.fail_no_game", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.save.fail_unknown", locale)
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

    async def load(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "GameNotStarted":
                        raise GameNotStarted()
                    case "NoSaveState":
                        raise NoSaveState()
                    case _:
                        raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.gaming_room.load.success",
                        lang=locale
                    )
                )
            except GameNotStarted:
                await self.reply_error(response, "response.gaming_room.load.fail_no_game", locale)
            except NoSaveState:
                await self.reply_error(response, "response.gaming_room.load.fail_no_save", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.load.fail_unknown", locale)
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

    async def rewind(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                match error:
                    case None:
                        pass
                    case "GameNotStarted":
                        raise GameNotStarted()
                    case "NoPreviousState":
                        raise NoPreviousState()
                    case _:
                        raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.gaming_room.rewind.success",
                        lang=locale
                    )
                )
            except GameNotStarted:
                await self.reply_error(response, "response.gaming_room.rewind.fail_no_game", locale)
            except NoPreviousState:
                await self.reply_error(response, "response.gaming_room.rewind.fail_no_previous_state", locale)
            except Exception:
                await self.reply_error(response, "response.gaming_room.rewind.fail_unknown", locale)
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

    async def joypad(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)
        user_id: int | None = data.get("user_id", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)
            user = await self.bot.fetch_user(user_id)

            match channel:
                case DMChannel():
                    guild_id = "@me"
                case _:
                    guild_id = channel.guild.id

            prefix = f"https://discord.com/channels/{guild_id}/{channel.id}/{response.id}\n"

            try:
                match error:
                    case None:
                        pass
                    case "UnauthorizedJoypadAccess":
                        raise UnauthorizedJoypadAccess()
                    case "NotEnoughJoypads":
                        raise NotEnoughJoypads()
                    case _:
                        raise Exception()
            except UnauthorizedJoypadAccess:
                await self.dm_error(user, "response.gaming_room.play.fail_not_own_joypad", locale, prefix=prefix)
            except NotEnoughJoypads:
                await self.dm_error(user, "response.gaming_room.play.fail_not_enough_joypads", locale, prefix=prefix)
            except Exception:
                await self.dm_error(user, "response.gaming_room.play.fail_unknown", locale, prefix=prefix)
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
    async def dm_error(user: discord.User, message: str, lang, prefix="", suffix="", **kwargs):
        content = prefix
        content += translation_manager.translate_random(message, lang=lang, **kwargs)
        content += "\n"
        content += "-# "
        content += translation_manager.translate(f'{message}.error', lang=lang, **kwargs)
        content += suffix

        return await user.send(content=content, **kwargs)

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
    bot.add_cog(GamingRoomAPI(bot))
