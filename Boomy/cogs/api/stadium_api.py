import discord
from discord.ext import commands
from fastapi import status, APIRouter
from fastapi.responses import JSONResponse
from vault.data.characters import Celebrity
from vault.exceptions.berry_refuses_battle import BerryRefusesBattle
from vault.exceptions.cafe_refuses_battle import CafeRefusesBattle
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.invalid_attachment import InvalidAttachment
from vault.exceptions.invalid_pokemon_team import InvalidPokemonTeam
from vault.exceptions.jax_refuses_battle import JaxRefusesBattle
from vault.exceptions.no_pokemon_data import NoPokemonData
from vault.exceptions.opponent_has_no_pokemon_data import OpponentHasNoPokemonData
from vault.exceptions.user_cannot_challenge_self import UserCannotChallengeSelf

from cogs.storage_room import StorageRoom
from main import translation_manager


class StadiumAPI(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.router = APIRouter()
        self.router.add_api_route(
            "/stadium/battle",
            self.battle,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/stadium/register",
            self.register,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )
        self.router.add_api_route(
            "/stadium/info",
            self.info,
            status_code=status.HTTP_204_NO_CONTENT,
            methods=["POST"]
        )

    async def battle(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)
        opponent_id: int | None = data.get("opponent_id", None)
        winner_id: int | None = data.get("winner_id", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                if error is not None:
                    match error:
                        case "CafeRefusesBattle":
                            raise CafeRefusesBattle()
                        case "BerryRefusesBattle":
                            raise BerryRefusesBattle()
                        case "JaxRefusesBattle":
                            raise JaxRefusesBattle()
                        case "UserCannotChallengeSelf":
                            raise UserCannotChallengeSelf()
                        case "NoPokemonData":
                            raise NoPokemonData()
                        case "OpponentHasNoPokemonData":
                            raise OpponentHasNoPokemonData()
                        case _:
                            raise Exception()

                if winner_id is not None:
                    winner = await self.bot.fetch_user(winner_id)
                    content = "response.stadium.battle.finished"

                    match winner.id:
                        case Celebrity.Boomy.value:
                            content += ".boomy"

                    await response.reply(
                        content=translation_manager.translate_random(
                            content=content, lang=locale,
                            winner=winner.display_name
                        )
                    )
                else:
                    content = "response.stadium.battle.ready"

                    match opponent_id:
                        case Celebrity.Boomy.value:
                            content += ".boomy"

                    await response.reply(
                        content=translation_manager.translate_random(
                            content=content, lang=locale
                        )
                    )
            except CafeRefusesBattle:
                await self.reply_error(response, "response.stadium.battle.fail_cafe_refuses", locale)
            except BerryRefusesBattle:
                await self.reply_error(response, "response.stadium.battle.fail_berry_refuses", locale)
            except JaxRefusesBattle:
                await self.reply_error(response, "response.stadium.battle.fail_jax_refuses", locale)
            except UserCannotChallengeSelf:
                await self.reply_error(response, "response.stadium.battle.fail_challenge_self", locale)
            except NoPokemonData:
                await self.reply_error(response, "response.stadium.battle.fail_no_pkmn", locale)
            except OpponentHasNoPokemonData:
                await self.reply_error(response, "response.stadium.battle.fail_opponent_no_pkmn", locale)
            except Exception:
                await self.reply_error(response, "response.stadium.battle.fail_unknown", locale)
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

    async def register(self, data: dict):
        channel_id: int | None = data.get("channel_id", None)
        response_id: int | None = data.get("response_id", None)
        locale: int | None = data.get("locale", None)
        error: str | None = data.get("error", None)
        species: str | None = data.get("species", None)
        winner_id: int | None = data.get("winner_id", None)

        try:
            channel = await self.bot.fetch_channel(channel_id)
            response = await channel.fetch_message(response_id)

            try:
                if error is not None:
                    match error:
                        case "InvalidAttachment":
                            raise InvalidAttachment()
                        case "InvalidPokemonTeam":
                            raise InvalidPokemonTeam()
                        case _:
                            raise Exception()

                content = "response.stadium.register.success"

                if species is not None:
                    species = species.lower()

                match species:
                    case "zorua":
                        content += ".zorua"

                winner = await self.bot.fetch_user(winner_id)

                match winner.id:
                    case Celebrity.Boomy.value:
                        content += ".boomy_win"
                    case _:
                        content += ".boomy_lose"

                await response.reply(
                    content=translation_manager.translate_random(
                        content=content, lang=locale,
                        winner=winner.display_name
                    )
                )
            except InvalidAttachment:
                await self.reply_error(response, "response.stadium.register.fail_invalid_attachment", locale)
            except InvalidPokemonTeam:
                await self.reply_error(response, "response.stadium.register.fail_invalid_team", locale)
            except Exception:
                await self.reply_error(response, "response.stadium.register.fail_unknown", locale)
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

    async def info(self, data: dict):
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
                        case "NoPokemonData":
                            raise NoPokemonData()
                        case _:
                            raise Exception()

                await response.reply(
                    content=translation_manager.translate_random(
                        "response.stadium.info.success",
                        lang=locale
                    )
                )
            except NoPokemonData:
                await self.reply_error(response, "response.stadium.info.fail_no_pkmn", locale)
            except Exception:
                await self.reply_error(response, "response.stadium.info.fail_unknown", locale)
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
    bot.add_cog(StadiumAPI(bot))
