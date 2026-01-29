from typing import Any

import discord
import requests
from discord.ext import commands
from poke_env import ServerConfiguration
from poke_env.teambuilder import TeambuilderPokemon
from vault.data.characters import Celebrity, Characters
from vault.exceptions.berry_refuses_battle import BerryRefusesBattle
from vault.exceptions.boomy_refuses_battle import BoomyRefusesBattle
from vault.exceptions.cafe_refuses_battle import CafeRefusesBattle
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.invalid_attachment import InvalidAttachment
from vault.exceptions.invalid_pokemon_team import InvalidPokemonTeam
from vault.exceptions.jax_refuses_battle import JaxRefusesBattle
from vault.exceptions.no_pokemon_data import NoPokemonData
from vault.exceptions.opponent_has_no_pokemon_data import OpponentHasNoPokemonData
from vault.exceptions.user_cannot_challenge_self import UserCannotChallengeSelf

from cogs.maintenance_room import MaintenanceRoom
from cogs.storage_room import StorageRoom
from config import Config
from main import translation_manager
from pokemon.players.boomy_player import BoomyPlayer
from pokemon.players.discord_random_player import DiscordRandomPlayer
from pokemon.single_mon_teambuilder import SingleMonTeambuilder


class Stadium(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.battles: dict[int, int] = dict()

    # stadium = discord.SlashCommandGroup(
    #     name="stadium"
    # )

    # @stadium.command(
    #     name="battle",
    #     description="Battle another user using your saved Pokémon"
    # )
    async def battle(self, ctx: discord.ApplicationContext, who: discord.User):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "opponent_id": who.id,
            "winner_id": None
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if not user.pokemon.mon:
            raise NoPokemonData()

        user_team = SingleMonTeambuilder(user.pokemon.mon)

        match who.id:
            case ctx.author.id:
                raise UserCannotChallengeSelf()
            case self.bot.user.id:
                raise CafeRefusesBattle()
            case Celebrity.Boomy.value:
                opponent_team = SingleMonTeambuilder(Characters.Boomy["pokemon"])
            case Celebrity.Berry.value:
                raise BerryRefusesBattle()
            case Celebrity.Jax.value:
                raise JaxRefusesBattle()
            case _:
                opponent = self.storage_room_cog.user_database.fetch_or_register(who.id)

                if not opponent.pokemon.mon:
                    raise OpponentHasNoPokemonData()

                opponent_team = SingleMonTeambuilder(opponent.pokemon.mon)

        # f"Interactive battle: {interaction.user.display_name} vs {opponent.display_name}"
        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.stadium.battle.loading", lang=ctx.interaction.locale,
                user=ctx.author.display_name, opponent=who.display_name
            )
        )

        data["response_id"] = response.id

        server_cfg = ServerConfiguration(Config.SHOWDOWN_SERVER, "https://play.pokemonshowdown.com/action.php?")

        p1 = DiscordRandomPlayer(
            server_configuration=server_cfg,
            battle_format="[Gen 9] Boomy's Gaming Cafe",
            team=user_team,
            message=response
        )

        match who.id:
            case Celebrity.Boomy.value:
                p2 = BoomyPlayer(
                    server_configuration=server_cfg,
                    battle_format="[Gen 9] Boomy's Gaming Cafe",
                    team=opponent_team,
                    message=response
                )
            case _:
                p2 = DiscordRandomPlayer(
                    server_configuration=server_cfg,
                    battle_format="[Gen 9] Boomy's Gaming Cafe",
                    team=opponent_team,
                    message=response
                )

        await response.edit(
            content=translation_manager.translate_random(
                "response.stadium.battle.ready", lang=ctx.interaction.locale,
                user=ctx.author.display_name, opponent=who.display_name
            )
        )

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/battle",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

        await p1.battle_against(p2, n_battles=1)

        winner = None

        if p1.n_won_battles > p2.n_won_battles:
            winner = ctx.author
        elif p2.n_won_battles > p1.n_won_battles:
            winner = who

        await response.followup.send(
            content=translation_manager.translate_random(
                "response.stadium.battle.finished", lang=ctx.interaction.locale,
                user=ctx.author.display_name, opponent=who.display_name,
                winner=winner.display_name
            )
        )

        if winner is not None:
            data["winner_id"] = winner.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/battle",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    # @battle.error
    async def on_battle_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case CafeRefusesBattle():
                data["error"] = "CafeRefusesBattle"
            case BoomyRefusesBattle():
                data["error"] = "BoomyRefusesBattle"
            case BerryRefusesBattle():
                data["error"] = "BerryRefusesBattle"
            case JaxRefusesBattle():
                data["error"] = "JaxRefusesBattle"
            case UserCannotChallengeSelf():
                data["error"] = "UserCannotChallengeSelf"
            case NoPokemonData():
                # "You haven't imported a Pokémon yet."
                data["error"] = "NoPokemonData"
            case OpponentHasNoPokemonData():
                # "Both users must import a Pokémon with /import_pokemon."
                data["error"] = "OpponentHasNoPokemonData"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case None:
                message = None
            case "CafeRefusesBattle":
                message = "response.stadium.battle.fail_cafe_refuses"
            case "BoomyRefusesBattle":
                message = "response.stadium.battle.fail_boomy_refuses"
            case "BerryRefusesBattle":
                message = "response.stadium.battle.fail_berry_refuses"
            case "JaxRefusesBattle":
                message = "response.stadium.battle.fail_jax_refuses"
            case "UserCannotChallengeSelf":
                message = "response.stadium.battle.fail_challenge_self"
            case "NoPokemonData":
                message = "response.stadium.battle.fail_no_pkmn"
            case "OpponentHasNoPokemonData":
                message = "response.stadium.battle.fail_opponent_no_pkmn"
            case _:
                message = "response.stadium.battle.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/battle",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    # @stadium.command(
    #     name="register",
    #     description="Register or replace your Pokémon (Showdown team format)"
    # )
    # @option(
    #     input_type=discord.SlashCommandOptionType.attachment,
    #     name="file",
    #     # description="",
    #     required=True
    # )
    async def register(self, ctx: discord.ApplicationContext, file: discord.Attachment):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "species": None,
            "winner_id": None
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if "text/plain" not in file.content_type:
            raise InvalidAttachment()

        file_bytes = await file.read()
        pokemon = "\n".join(file_bytes.decode("utf-8").splitlines())

        try:
            mon = TeambuilderPokemon.from_showdown(pokemon)
            data["species"] = mon.species
        except ValueError:
            raise InvalidPokemonTeam()

        user.pokemon.mon = pokemon

        user_team = SingleMonTeambuilder(user.pokemon.mon)
        opponent_team = SingleMonTeambuilder(Characters.Boomy["pokemon"])

        server_cfg = ServerConfiguration(Config.SHOWDOWN_SERVER, "https://play.pokemonshowdown.com/action.php?")

        p1 = DiscordRandomPlayer(
            server_configuration=server_cfg,
            battle_format="[Gen 8] Boomy's Gaming Cafe",
            team=user_team
        )

        p2 = BoomyPlayer(
            server_configuration=server_cfg,
            battle_format="[Gen 8] Boomy's Gaming Cafe",
            team=opponent_team
        )

        await p1.battle_against(p2, n_battles=1)

        winner = None

        if p1.n_won_battles > p2.n_won_battles:
            winner = ctx.author
        elif p2.n_won_battles > p1.n_won_battles:
            winner = self.bot.user

        if winner is None:
            raise InvalidPokemonTeam()

        data["winner_id"] = winner.id

        self.storage_room_cog.user_database.update(user.id, user)

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.stadium.register.success", lang=ctx.interaction.locale
            )
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/register",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    # @register.error
    async def on_register_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case InvalidAttachment():
                data["error"] = "InvalidAttachment"
            case InvalidPokemonTeam():
                data["error"] = "InvalidPokemonTeam"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "InvalidAttachment":
                message = "response.stadium.register.fail_invalid_attachment"
            case "InvalidPokemonTeam":
                message = "response.stadium.register.fail_invalid_team"
            case _:
                message = "response.stadium.register.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/register",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    # @stadium.command(
    #     name="info",
    #     description="Show your saved Pokémon"
    # )
    async def info(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if not user.pokemon.mon:
            raise NoPokemonData()

        # f"Format `{fmt}`\n" + fmt_block(team_str)
        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.stadium.info.success", lang=ctx.interaction.locale,
                pokemon=user.pokemon.mon
            )
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/info",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    # @info.error
    async def on_info_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case NoPokemonData():
                # "You haven't imported a Pokémon yet."
                data["error"] = "NoPokemonData"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "NoPokemonData":
                message = "response.stadium.info.fail_no_pkmn"
            case _:
                message = "response.stadium.info.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/stadium/info",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @staticmethod
    async def respond_error(interaction: discord.Interaction, message: str, lang, prefix="", suffix="", **kwargs):
        content = prefix
        content += translation_manager.translate_random(message, lang=lang, **kwargs)
        content += "\n"
        content += "-# "
        content += translation_manager.translate(f'{message}.error', lang=lang, **kwargs)
        content += suffix

        return await interaction.respond(content=content, **kwargs)

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

    @property
    def maintenance_room_cog(self):
        maintenance_room_cog: MaintenanceRoom | None = self.bot.get_cog("MaintenanceRoom")

        if maintenance_room_cog is None:
            raise CogNotRegistered()

        return maintenance_room_cog


def setup(bot):
    bot.add_cog(Stadium(bot))
