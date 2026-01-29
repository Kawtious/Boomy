from typing import Type, Any

import discord
import requests
from PIL import Image
from discord import option, DMChannel, ButtonStyle
from discord.ext import commands
from discord.ui import View
from vault.data.characters import Celebrity
from vault.data.consoles import Console
from vault.data.database.cartridge import Cartridge
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.user import User
from vault.exceptions.berry_refuses_invite import BerryRefusesInvite
from vault.exceptions.boomy_refuses_invite import BoomyRefusesInvite
from vault.exceptions.cafe_refuses_invite import CafeRefusesInvite
from vault.exceptions.cartridge_not_found import GameNotStarted
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.console_not_valid import ConsoleNotValid
from vault.exceptions.game_does_not_exist import GameDoesNotExist
from vault.exceptions.invalid_frame_data import InvalidFrameData
from vault.exceptions.jax_refuses_invite import JaxRefusesInvite
from vault.exceptions.last_message_not_found import LastMessageNotFound
from vault.exceptions.no_previous_state import NoPreviousState
from vault.exceptions.no_save_state import NoSaveState
from vault.exceptions.not_enough_joypads import NotEnoughJoypads
from vault.exceptions.unauthorized_joypad_access import UnauthorizedJoypadAccess
from vault.exceptions.user_already_invited import UserAlreadyInvited
from vault.exceptions.user_is_cartridge_owner import UserIsCartridgeOwner

from cogs.maintenance_room import MaintenanceRoom
from cogs.storage_room import StorageRoom
from config import Config
from data.gaming_session import GamingSession
from emulator.base_emulator import BaseEmulator
from emulator.game.base_game_instance import BaseGameInstance
from emulator.gameboy_emulator import GameBoyEmulator
from emulator.nes_emulator import NESEmulator
from main import translation_manager
from utils.discord_utils import image_to_embed, gif_to_embed
from utils.frame_utils import FrameUtils


class GamingRoom(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.gameboy_emulator = GameBoyEmulator()
        self.nes_emulator = NESEmulator()
        self.sessions: dict[int, GamingSession] = dict()

    async def cog_load(self):
        pass

    async def cog_unload(self):
        self.gameboy_emulator.game_instance_manager.shutdown()
        self.nes_emulator.game_instance_manager.shutdown()

    @discord.slash_command(
        name="play",
        description="Boomy will fetch your game from the Vault and boot it on its proper console."
    )
    @option(
        input_type=discord.SlashCommandOptionType.string,
        name="title",
        description="Name the game so Boomy can sniff it out in her Vault.",
        required=True
    )
    @option(
        input_type=discord.SlashCommandOptionType.string,
        name="console",
        description="Which console should Boomy fire up?",
        choices=[str(console) for console in Console],
        required=True
    )
    async def play(self, ctx: discord.ApplicationContext, title: str, console: str):
        """
        Ask Boomy to load a game from the Game Vault™.
        :param ctx:
        :param title:
        :param console:
        :return:
        """
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            self.sessions[user.id] = {
                "emulator": None,
                "joypad": None,
                "message": None
            }

        match console:
            case Console.Pikapalette.value:
                emulator = self.gameboy_emulator
                cartridge = self.storage_room_cog.cartridge_database.fetch_gameboy_cartridge(user, title)
                game_instance, frame = await self.__start_game(emulator, cartridge, user)
                joypad = self.__build_gameboy_joypad(emulator, cartridge, user)
            case Console.PonytaEntertainmentSystem.value:
                emulator = self.nes_emulator
                cartridge = self.storage_room_cog.cartridge_database.fetch_nes_cartridge(user, title)
                game_instance, frame = await self.__start_game(emulator, cartridge, user)
                joypad = self.__build_nes_joypad(emulator, cartridge, user)

                # These save states must be reset, otherwise loading them causes a 0xC0000005 error
                cartridge.state = None
                cartridge.save_state = None
            case _:
                raise ConsoleNotValid()

        self.storage_room_cog.user_database.update(user.id, user)

        image_bytes = FrameUtils.frame_to_bytes(frame)
        file, embed = image_to_embed(image_bytes)

        if self.sessions[user.id]["message"] is not None:
            try:
                await self.sessions[user.id]["message"].delete()
            except discord.HTTPException:
                pass

        self.sessions[user.id] = {
            "emulator": emulator,
            "joypad": joypad
        }

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.gaming_room.play.success", lang=ctx.interaction.locale
            ),
            file=file,
            embed=embed,
            view=self.sessions[user.id]["joypad"]
        )

        data["response_id"] = response.id

        self.sessions[user.id]["message"] = response

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/play",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @play.error
    async def on_play_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case GameDoesNotExist():
                data["error"] = "GameDoesNotExist"
            case InvalidFrameData():
                data["error"] = "InvalidFrameData"
            case ConsoleNotValid():
                data["error"] = "ConsoleNotValid"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case None:
                message = None
            case "GameDoesNotExist":
                message = "response.gaming_room.play.fail_not_found"
            case "InvalidFrameData":
                message = "response.gaming_room.play.fail_console_broke"
            case "ConsoleNotValid":
                message = "response.gaming_room.play.fail_invalid_console"
            case _:
                message = "response.gaming_room.play.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/play",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @discord.slash_command(
        name="invite",
        description="Let Boomy grant a friend permission to touch your sacred joypad."
    )
    @option(
        input_type=discord.SlashCommandOptionType.user,
        name="who",
        description="Who’s lucky enough to get your joypad rights? Point Boomy to them!",
        required=True
    )
    async def invite(self, ctx: discord.ApplicationContext, who: discord.User):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            raise GameNotStarted()

        match who.id:
            case ctx.author.id:
                raise UserIsCartridgeOwner()
            case self.bot.user.id:
                raise CafeRefusesInvite()
            case Celebrity.Boomy.value:
                raise BoomyRefusesInvite()
            case Celebrity.Berry.value:
                raise BerryRefusesInvite()
            case Celebrity.Jax.value:
                raise JaxRefusesInvite()

        game = self.sessions[user.id]

        invited_user = self.storage_room_cog.user_database.fetch_or_register(who.id)

        cartridge, instance, users = game["emulator"].game_instance_manager.get_instance_from_user(user)

        game["emulator"].game_instance_manager.add_user(cartridge, invited_user)

        match game["message"].channel:
            case DMChannel():
                guild_id = "@me"
            case _:
                guild_id = game["message"].channel.guild.id

        message_link = f"https://discord.com/channels/{guild_id}/{game['message'].channel.id}/{game['message'].id}"

        content = f"<@{who.id}> — {message_link}"
        content += "\n"
        content += translation_manager.translate_random(
            "response.gaming_room.invite.success", lang=ctx.interaction.locale
        )

        response = await ctx.respond(
            content=content
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/invite",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @invite.error
    async def on_invite_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case CafeRefusesInvite():
                data["error"] = "CafeRefusesInvite"
            case BoomyRefusesInvite():
                data["error"] = "BoomyRefusesInvite"
            case BerryRefusesInvite():
                data["error"] = "BerryRefusesInvite"
            case JaxRefusesInvite():
                data["error"] = "JaxRefusesInvite"
            case GameNotStarted():
                data["error"] = "GameNotStarted"
            case NotEnoughJoypads():
                data["error"] = "NotEnoughJoypads"
            case UserIsCartridgeOwner():
                data["error"] = "UserIsCartridgeOwner"
            case UserAlreadyInvited():
                data["error"] = "UserAlreadyInvited"
            case LastMessageNotFound():
                data["error"] = "LastMessageNotFound"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "CafeRefusesInvite":
                message = "response.gaming_room.invite.fail_cafe_refuses"
            case "BoomyRefusesInvite":
                message = "response.gaming_room.invite.fail_boomy_refuses"
            case "BerryRefusesInvite":
                message = "response.gaming_room.invite.fail_berry_refuses"
            case "JaxRefusesInvite":
                message = "response.gaming_room.invite.fail_jax_refuses"
            case "GameNotStarted":
                message = "response.gaming_room.invite.fail_no_game"
            case "NotEnoughJoypads":
                message = "response.gaming_room.invite.fail_not_enough_joypads"
            case "UserIsCartridgeOwner":
                message = "response.gaming_room.invite.fail_invited_self"
            case "UserAlreadyInvited":
                message = "response.gaming_room.invite.fail_already_invited"
            case "LastMessageNotFound":
                message = "response.gaming_room.invite.fail_msg_not_found"
            case _:
                message = "response.gaming_room.invite.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            match data["error"]:
                case "BoomyRefusesInvite":
                    requests.post(
                        f"{Config.BOOMY_API}/gaming-room/invite",
                        json=data
                    )
                case "BerryRefusesInvite":
                    requests.post(
                        f"{Config.BERRY_API}/gaming-room/invite",
                        json=data
                    )
                case "JaxRefusesInvite":
                    requests.post(
                        f"{Config.JAX_API}/gaming-room/invite",
                        json=data
                    )
                case _:
                    requests.post(
                        f"{Config.BOOMY_API}/gaming-room/invite",
                        json=data
                    )
        except requests.exceptions.ConnectionError:
            pass

    @discord.slash_command(
        name="restart",
        description="Boomy smacks the reset button—your game and console start fresh, no snacks included!"
    )
    async def restart(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            raise GameNotStarted()

        game = self.sessions[user.id]

        cartridge, instance, users = game["emulator"].game_instance_manager.get_instance_from_user(user)

        instance.restart()
        cartridge.state = instance.save_state

        game_instance, frame = await self.__start_game(game["emulator"], cartridge, user)

        self.storage_room_cog.user_database.update(user.id, user)

        image_bytes = FrameUtils.frame_to_bytes(frame)
        file, embed = image_to_embed(image_bytes)

        if self.sessions[user.id]["message"] is not None:
            try:
                await self.sessions[user.id]["message"].delete()
            except discord.HTTPException:
                pass

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.gaming_room.restart.success", lang=ctx.interaction.locale
            ),
            file=file,
            embed=embed,
            view=self.sessions[user.id]["joypad"]
        )

        data["response_id"] = response.id

        self.sessions[user.id]["message"] = response

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/restart",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @restart.error
    async def on_restart_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case GameNotStarted():
                data["error"] = "GameNotStarted"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "GameNotStarted":
                message = "response.gaming_room.restart.fail_no_game"
            case _:
                message = "response.gaming_room.restart.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/restart",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @discord.slash_command(
        name="save",
        description="Boomy tucks your save into the Vault—safe from glitches, snacks, and sneaky paws!"
    )
    async def save(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            raise GameNotStarted()

        game = self.sessions[user.id]

        cartridge, instance, users = game["emulator"].game_instance_manager.get_instance_from_user(user)

        cartridge.save_state = instance.save_state

        self.storage_room_cog.user_database.update(user.id, user)

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.gaming_room.save.success", lang=ctx.interaction.locale
            )
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/save",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @save.error
    async def on_save_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case GameNotStarted():
                data["error"] = "GameNotStarted"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "GameNotStarted":
                message = "response.gaming_room.save.fail_no_game"
            case _:
                message = "response.gaming_room.save.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/save",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @discord.slash_command(
        name="load",
        description="Boomy pulls your save from the Vault—ta-da! Like it never exploded in the first place!"
    )
    async def load(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            raise GameNotStarted()

        game = self.sessions[user.id]

        cartridge, instance, users = game["emulator"].game_instance_manager.get_instance_from_user(user)

        if cartridge.save_state is None:
            raise NoSaveState()

        cartridge.state = cartridge.save_state

        game_instance, frame = await self.__start_game(game["emulator"], cartridge, user)

        self.storage_room_cog.user_database.update(user.id, user)

        image_bytes = FrameUtils.frame_to_bytes(frame)
        file, embed = image_to_embed(image_bytes)

        if self.sessions[user.id]["message"] is not None:
            try:
                await self.sessions[user.id]["message"].delete()
            except discord.HTTPException:
                pass

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.gaming_room.load.success", lang=ctx.interaction.locale
            ),
            file=file,
            embed=embed,
            view=self.sessions[user.id]["joypad"]
        )

        data["response_id"] = response.id

        self.sessions[user.id]["message"] = response

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/load",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @load.error
    async def on_load_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case GameNotStarted():
                data["error"] = "GameNotStarted"
            case NoSaveState():
                data["error"] = "NoSaveState"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "GameNotStarted":
                message = "response.gaming_room.load.fail_no_game"
            case "NoSaveState":
                message = "response.gaming_room.load.fail_no_save"
            case _:
                message = "response.gaming_room.load.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/load",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @discord.slash_command(
        name="rewind",
        description="Boomy boots up your last save! No judgment on how badly you were losing."
    )
    async def rewind(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        if user.id not in self.sessions:
            raise GameNotStarted()

        game = self.sessions[user.id]

        cartridge, instance, users = game["emulator"].game_instance_manager.get_instance_from_user(user)

        instance.previous_state()
        cartridge.state = instance.save_state

        game_instance, frame = await self.__start_game(game["emulator"], cartridge, user)

        self.storage_room_cog.user_database.update(user.id, user)

        image_bytes = FrameUtils.frame_to_bytes(frame)
        file, embed = image_to_embed(image_bytes)

        if self.sessions[user.id]["message"] is not None:
            try:
                await self.sessions[user.id]["message"].delete()
            except discord.HTTPException:
                pass

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.gaming_room.rewind.success", lang=ctx.interaction.locale
            ),
            file=file,
            embed=embed,
            view=self.sessions[user.id]["joypad"]
        )

        data["response_id"] = response.id

        self.sessions[user.id]["message"] = response

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/rewind",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    @rewind.error
    async def on_rewind_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case GameNotStarted():
                data["error"] = "GameNotStarted"
            case NoPreviousState():
                data["error"] = "NoPreviousState"
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "GameNotStarted":
                message = "response.gaming_room.rewind.fail_no_game"
            case "NoPreviousState":
                message = "response.gaming_room.rewind.fail_no_previous_state"
            case _:
                message = "response.gaming_room.rewind.fail_unknown"

        response = await self.respond_error(
            interaction=ctx.interaction,
            message=message,
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        try:
            requests.post(
                f"{Config.BOOMY_API}/gaming-room/rewind",
                json=data
            )
        except requests.exceptions.ConnectionError:
            pass

    async def repair_submit(self, ctx: discord.ApplicationContext):
        """
        Give Boomy a “broken” game for repair (he might prank-repair it into something ridiculous).
        :param ctx:
        :return:
        """
        raise NotImplemented()

    async def trade(self, ctx: discord.ApplicationContext):
        """
        Swap games with other patrons via Boomy as the middle-Zorua.
        :param ctx:
        :return:
        """
        raise NotImplemented()

    async def mystery(self, ctx: discord.ApplicationContext):
        """
        Boomy picks a random game for you to play.
        :param ctx:
        :return:
        """
        raise NotImplemented()

    async def random(self, ctx: discord.ApplicationContext):
        """
        Pull a completely random game from the vault for surprise play.
        :param ctx:
        :return:
        """
        raise NotImplemented()

    @staticmethod
    async def __start_game(
            emulator: BaseEmulator,
            cartridge: Cartridge,
            user: User
    ) -> tuple[BaseGameInstance, Image]:
        return emulator.start(cartridge, user)

    @staticmethod
    async def __play_game(
            emulator: BaseEmulator,
            cartridge: Cartridge,
            user: User,
            button=None
    ) -> tuple[BaseGameInstance, list[Image]]:
        return emulator.input(cartridge=cartridge, user=user, button=button)

    def __build_gameboy_joypad(
            self, emulator: GameBoyEmulator, cartridge: GameBoyCartridge, user: User | Type[User]
    ) -> View:
        return self.__build_joypad(
            layout=[
                "empty", "up", "empty", "empty", "a",
                "left", "down", "right", "b", "empty",
                "empty", "select", "empty", "start", "empty",
                "frame 1", "frame 10", "frame 30", "frame 60", "empty"
            ],
            style={
                "up": discord.ButtonStyle.primary,
                "down": discord.ButtonStyle.primary,
                "left": discord.ButtonStyle.primary,
                "right": discord.ButtonStyle.primary,
                "a": discord.ButtonStyle.green,
                "b": discord.ButtonStyle.red,
                "start": discord.ButtonStyle.secondary,
                "select": discord.ButtonStyle.secondary,
                "frame 1": discord.ButtonStyle.green,
                "frame 10": discord.ButtonStyle.green,
                "frame 30": discord.ButtonStyle.green,
                "frame 60": discord.ButtonStyle.green
            },
            emulator=emulator,
            cartridge=cartridge,
            owner=user
        )

    def __build_nes_joypad(self, emulator: NESEmulator, cartridge: NESCartridge, owner: User | Type[User]) -> View:
        return self.__build_joypad(
            layout=[
                "empty", "up", "empty", "b", "a",
                "left", "down", "right", "select", "start",
                "frame 1", "frame 10", "frame 30", "frame 60", "empty"
            ],
            style={
                "up": discord.ButtonStyle.primary,
                "down": discord.ButtonStyle.primary,
                "left": discord.ButtonStyle.primary,
                "right": discord.ButtonStyle.primary,
                "a": discord.ButtonStyle.red,
                "b": discord.ButtonStyle.red,
                "start": discord.ButtonStyle.secondary,
                "select": discord.ButtonStyle.secondary,
                "frame 1": discord.ButtonStyle.green,
                "frame 10": discord.ButtonStyle.green,
                "frame 30": discord.ButtonStyle.green,
                "frame 60": discord.ButtonStyle.green
            },
            emulator=emulator,
            cartridge=cartridge,
            owner=owner
        )

    def __build_joypad(
            self,
            layout,
            style: dict[str, ButtonStyle],
            owner: User | Type[User],
            emulator: BaseEmulator,
            cartridge: Cartridge
    ) -> View:
        view = View(timeout=None)

        for index, action in enumerate(layout):
            row = index // 5

            if action == "empty":
                view.add_item(
                    discord.ui.Button(
                        label="\u200b",
                        style=discord.ButtonStyle.secondary,
                        disabled=True,
                        row=row
                    )
                )
                continue

            button = discord.ui.Button(
                label=action.capitalize(),
                style=style.get(action, discord.ButtonStyle.secondary),
                row=row,
                custom_id=f"joypad:{action}"
            )

            def __make_press_callback(button: str):
                async def on_button_press(interaction: discord.Interaction):
                    await self.__press_joypad(interaction, view, owner, emulator, cartridge, button)

                return on_button_press

            button.callback = __make_press_callback(action)
            view.add_item(button)

        return view

    async def __press_joypad(
            self,
            interaction: discord.Interaction,
            view: View,
            owner: User | Type[User],
            emulator: BaseEmulator,
            cartridge: Cartridge,
            button: str
    ):
        await interaction.response.defer()

        data: dict[str, Any] = {
            "channel_id": interaction.channel.id,
            "response_id": interaction.message.id,
            "locale": interaction.locale,
            "error": None,
            "user_id": interaction.user.id
        }

        try:
            user = self.storage_room_cog.user_database.fetch_or_register(interaction.user.id)

            game_instance, frames = await self.__play_game(emulator, cartridge, user, button)

            self.storage_room_cog.user_database.update(owner.id, owner)

            if len(frames) == 1:
                image_bytes = FrameUtils.frame_to_bytes(frames[0])
                file, embed = image_to_embed(image_bytes)
            else:
                gif_bytes = FrameUtils.frames_to_bytes(frames)
                file, embed = gif_to_embed(gif_bytes)

            await interaction.message.edit(
                content=interaction.message.content,
                file=file,
                embed=embed,
                view=view
            )
        except UnauthorizedJoypadAccess:
            data["error"] = "UnauthorizedJoypadAccess"
        except NotEnoughJoypads:
            data["error"] = "NotEnoughJoypads"
        except Exception:
            data["error"] = "Exception"
            await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case None:
                error = None
            case "UnauthorizedJoypadAccess":
                error = "response.gaming_room.play.fail_not_own_joypad"
            case "NotEnoughJoypads":
                error = "response.gaming_room.play.fail_not_enough_joypads"
            case _:
                error = "response.gaming_room.play.fail_unknown"

        if error is not None:
            await interaction.followup.send(
                ephemeral=True,
                content=translation_manager.translate_random(error, lang=interaction.locale)
            )

            try:
                requests.post(
                    f"{Config.BOOMY_API}/gaming-room/joypad",
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


__gaming_room_cog: GamingRoom | None = None


def setup(bot):
    global __gaming_room_cog

    __gaming_room_cog = GamingRoom(bot)
    bot.add_cog(__gaming_room_cog)

    bot.loop.create_task(__gaming_room_cog.cog_load())


def teardown(bot):
    global __gaming_room_cog

    if not __gaming_room_cog:
        return

    bot.loop.create_task(__gaming_room_cog.cog_unload())
    __gaming_room_cog = None
