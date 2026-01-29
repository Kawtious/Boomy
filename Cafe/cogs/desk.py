import os
import tempfile
from typing import Any

import cynes
import discord
import requests
from discord import option
from discord.ext import commands
from pyboy import PyBoy
from pyboy.utils import PyBoyException
from sqlalchemy.exc import IntegrityError
from vault.data.consoles import Console
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.user import User
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.console_not_valid import ConsoleNotValid
from vault.exceptions.game_already_registered import GameAlreadyRegistered
from vault.exceptions.invalid_rom import InvalidROM

from cogs.maintenance_room import MaintenanceRoom
from cogs.storage_room import StorageRoom
from config import Config
from main import translation_manager


class Desk(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(
        name="checkin",
        description="Hand Boomy your game for safe-keeping in her legendary Game Vault™."
    )
    @option(
        input_type=discord.SlashCommandOptionType.string,
        name="title",
        description="What’s the game’s name? Boomy needs it for her Vault labels.",
        required=True
    )
    @option(
        input_type=discord.SlashCommandOptionType.string,
        name="console",
        description="Which console plays this beauty?",
        choices=[str(console) for console in Console],
        required=True
    )
    @option(
        input_type=discord.Attachment,
        name="cartridge",
        description="Did you actually bring the cartridge, or is this a ghost game?",
        required=True
    )
    async def checkin(
            self, ctx: discord.ApplicationContext,
            title: str, console: str, cartridge: discord.Attachment
    ):
        """
        Hand over a game to Boomy, so she can add it to the Game Vault™.
        :param ctx:
        :param title:
        :param console:
        :param cartridge:
        :return:
        """
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        rom_bytes = await cartridge.read()

        match console:
            case Console.Pikapalette.value:
                await self.__checkin_gameboy(user, title, rom_bytes)
            case Console.PonytaEntertainmentSystem.value:
                await self.__checkin_nes(user, title, rom_bytes)
            case _:
                raise ConsoleNotValid()

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.desk.checkin.success", lang=ctx.interaction.locale
            )
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/desk/check-in",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @checkin.error
    async def on_checkin_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case InvalidROM():
                data["error"] = "InvalidROM"
            case GameAlreadyRegistered():
                data["error"] = "GameAlreadyRegistered"
            case ConsoleNotValid():
                data["error"] = "ConsoleNotValid"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "InvalidROM":
                message = "response.desk.checkin.fail_invalid_cartridge"
            case "GameAlreadyRegistered":
                message = "response.desk.checkin.fail_already_checked_in"
            case "ConsoleNotValid":
                message = "response.desk.checkin.fail_invalid_console"
            case _:
                message = "response.desk.checkin.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/desk/check-in",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    async def __checkin_gameboy(self, user: User, title: str, rom_bytes: bytes):
        with tempfile.NamedTemporaryFile(dir=os.path.join(Config.PROJECT_ROOT, "temp"), delete=False) as tmp_file:
            tmp_file.write(rom_bytes)
            tmp_path = tmp_file.name

            try:
                emulator: PyBoy = PyBoy(
                    gamerom=tmp_path,
                    window="null"
                )

                emulator.stop(save=False)
            except PyBoyException:
                raise InvalidROM()

        cartridge: GameBoyCartridge = GameBoyCartridge(
            title=title,
            rom=rom_bytes
        )

        # Store ROM in database
        user.gameboy_cartridges.append(cartridge)

        try:
            self.storage_room_cog.user_database.update(user.id, user)
        except IntegrityError:
            raise GameAlreadyRegistered()

    async def __checkin_nes(self, user: User, title: str, rom_bytes: bytes):
        with tempfile.NamedTemporaryFile(dir=os.path.join(Config.PROJECT_ROOT, "temp"), delete=False) as tmp_file:
            tmp_file.write(rom_bytes)
            tmp_path = tmp_file.name

            try:
                cynes.NES(
                    rom=tmp_path
                )
            except RuntimeError:
                raise InvalidROM()

        cartridge: NESCartridge = NESCartridge(
            title=title,
            rom=rom_bytes
        )

        # Store ROM in database
        user.nes_cartridges.append(cartridge)

        try:
            self.storage_room_cog.user_database.update(user.id, user)
        except IntegrityError:
            raise GameAlreadyRegistered()

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
    bot.add_cog(Desk(bot))
