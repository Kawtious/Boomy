import asyncio
import json
import os
import random
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import aiohttp
import discord
from discord import option
from discord.ext import commands
from vault.data.characters import Celebrity
from vault.exceptions.ask_before_introduction import AskBeforeIntroduction
from vault.exceptions.ask_in_cooldown import AskInCooldown
from vault.exceptions.cog_not_registered import CogNotRegistered
from vault.exceptions.interrupted_ask import InterruptedAsk
from vault.exceptions.interrupted_introduction import InterruptedIntroduction
from vault.exceptions.interrupted_talk import InterruptedTalk

from cogs.maintenance_room import MaintenanceRoom
from cogs.storage_room import StorageRoom
from config import Config
from data.conversation import Conversation
from data.topics import Topics
from main import translation_manager


class Mood(Enum):
    Playful = 0,
    Sulky = 1,
    Hyper = 2,
    Sleepy = 3,
    Grumpy = 4,
    Focused = 5,
    Sneaky = 6


@dataclass
class Stats:
    # General cheer. Goes up from praise, fun events, food; down from boredom or losing.
    happiness: float = field(default=100, init=True)

    # Tolerance for users, glitches, or interruptions.
    patience: float = field(default=100, init=True)

    # How badly she needs snacks.
    hunger: float = field(default=0, init=True)

    # Physical/mental activity level.
    energy: float = field(default=100, init=True)

    # How focused she is on something else.
    distraction: float = field(default=0, init=True)

    # Gremlin factor.
    mischief: float = field(default=0, init=True)

    # Relationship strength with each client.
    trust: dict[int, float] = field(default_factory=dict)

    mood: list[Mood] = field(default_factory=list)


class Boomy(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.stats: Stats = Stats()
        self.ping_cooldowns: dict[int, float] = dict()
        self.conversations: dict[int, Conversation] = dict()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.bot.user.id:
            return

        if message.author.bot:
            return

        now = time.time()

        response: str | None = None

        if message.content.startswith(f"<@{self.bot.user.id}>"):
            match message.author.id:
                case Celebrity.Zark.value | Celebrity.Amethyst.value:
                    pass
                case _:
                    user = self.storage_room_cog.user_database.fetch_or_register(message.author.id)

                    if not user.premium and message.author.id in self.ping_cooldowns:
                        cooldown = 1 * 10
                        if now - self.ping_cooldowns[message.author.id] < cooldown:
                            return

            response = "response.ping"

            with open(
                    os.path.join(
                        translation_manager.locale_dir, translation_manager.language, "dictionaries",
                        "pings.json"
                    ),
                    "r",
                    encoding="utf-8"
            ) as f:
                pings_dictionary = json.load(f)

                ping_data = pings_dictionary.get(str(message.author.id), None)

                if ping_data is not None:
                    response += "." + ping_data["base"]
                else:
                    ping_data = pings_dictionary.get("_", None)

                if ping_data is not None:
                    branch = self.__find_branch(message.content.lower(), ping_data.get("keywords", {}))

                    if branch:
                        response += "." + branch

            self.ping_cooldowns[message.author.id] = now

        if response is None:
            return

        try:
            await message.reply(
                content=translation_manager.translate_random(response)
            )
        except Exception:
            await self.maintenance_room_cog.handle_exception()

    @discord.slash_command(
        name="ping"
    )
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "ping_time": time.time()
        }

        response = await ctx.respond(
            content=translation_manager.translate_random(
                "response.boomy.ping.success", lang=ctx.interaction.locale
            )
        )

        data["response_id"] = response.id

        await response.edit(
            content=translation_manager.translate_random(
                "response.boomy.ping.success_ms",
                lang=ctx.interaction.locale,
                ms=round((time.time() - data["ping_time"]) * 1000, 4)
            )
        )

        async def ping_them_creatures(url, sesh):
            try:
                await sesh.post(url, json=data)
            except Exception:
                pass

        creatures = [
            f"{Config.CAFE_API}/ping",
            f"{Config.BOOMY_API}/ping",
            f"{Config.BERRY_API}/ping",
            f"{Config.JAX_API}/ping",
        ]

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(ping_them_creatures(url, session) for url in creatures))

    @ping.error
    async def on_ping_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None
        }

        match exception.original:
            case Exception():
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        response = await self.respond_error(
            interaction=ctx.interaction,
            message="response.boomy.ping.fail_unknown",
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

        async def ping_them_creatures(url, sesh: aiohttp.ClientSession):
            try:
                await sesh.post(url, json=data)
            except Exception:
                pass

        creatures = [
            f"{Config.CAFE_API}/ping",
            f"{Config.BOOMY_API}/ping",
            f"{Config.BERRY_API}/ping",
            f"{Config.JAX_API}/ping",
        ]

        async with aiohttp.ClientSession() as session:
            await asyncio.gather(*(ping_them_creatures(url, session) for url in creatures))

    @discord.slash_command(
        name="talk",
        description="Strike up a chat with Boomy at the café."
    )
    @option(
        input_type=discord.SlashCommandOptionType.string,
        name="ask",
        description="What do you ask Boomy?",
        choices=[str(topic) for topic in Topics],
        required=False
    )
    async def talk(self, ctx: discord.ApplicationContext, ask: str):
        await ctx.defer()

        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale
        }

        user = self.storage_room_cog.user_database.fetch_or_register(ctx.author.id)

        now = time.time()

        if user.id not in self.conversations:
            self.conversations[user.id] = {
                "action": None,
                "story": None,
                "ask": None,
                "message": None,
                "index": 1,
                "reached_end": False,
                "interrupted": False,
                "last_time": now
            }

        state = self.conversations[user.id]

        cooldown = 10 * 60

        # Reset conversation if timeout exceeded
        if now - state["last_time"] > cooldown:
            state["action"] = None
            state["story"] = None
            state["ask"] = None
            state["message"] = None
            state["index"] = 1
            state["reached_end"] = False
            state["last_time"] = now

        action: str | None = None
        story: str | None = None

        # First time meeting Boomy
        if not user.statistics.met_boomy:
            action = "conversation.introduction"

            match user.id:
                case Celebrity.Zark.value:
                    story = "dad"
                case Celebrity.Amethyst.value:
                    story = "amethyst"
                case _:
                    if "ZORUA" in ctx.author.display_name.upper():
                        story = "another_zorua"
                    else:
                        story = "fresh_meat"

        # Already met Boomy
        if user.statistics.met_boomy:
            action = "conversation.talk"

            if ask:
                action += ".ask"

                match ask:
                    case Topics.Boomy.value:
                        action += ".about_boomy"
                        story = "intro" if not user.statistics.knows_boomy else random.choice(
                            ["1"]
                        )
                    case Topics.Cafe.value:
                        action += ".about_cafe"
                        story = "intro" if not user.statistics.knows_cafe else random.choice(
                            ["1"]
                        )
                    case Topics.Berry.value:
                        action += ".about_berry"
                        story = "intro" if not user.statistics.knows_berry else random.choice(
                            ["1"]
                        )
                    case Topics.Jax.value:
                        action += ".about_jax"
                        story = "intro" if not user.statistics.knows_jax else random.choice(
                            ["1"]
                        )
                    case Topics.Dad.value:
                        action += ".about_dad"
                        story = "intro" if not user.statistics.knows_dad else random.choice(
                            ["1"]
                        )
                    case Topics.MysteryConsole.value:
                        action += ".about_mystery_console"
                        story = "intro" if not user.statistics.knows_mystery_console else random.choice(
                            ["1"]
                        )
                    case Topics.BoomyEars.value:
                        action += ".about_boomy_ears"
                        story = "intro" if not user.statistics.knows_boomy_ears else random.choice(
                            ["1"]
                        )
            else:
                match user.id:
                    case Celebrity.Zark.value:
                        action += ".dad"
                        story = random.choice(
                            ["ate_yummy"]
                        )
                    case Celebrity.Amethyst.value:
                        action += ".amethyst"
                        story = random.choice(
                            ["1"]
                        )
                    case _:
                        action += ".random"
                        story = random.choice(
                            ["casual", "grumpy", "desk_duty", "late_night"]
                        )

        if not user.statistics.met_boomy and state["index"] <= 2 and ask:
            raise AskBeforeIntroduction()

        # Is Boomy talking?
        if state["action"] and not state["reached_end"] and ask and ask != state["ask"]:
            if "conversation.introduction" in state["action"]:
                raise InterruptedIntroduction()
            elif "conversation.talk.ask" in state["action"]:
                raise InterruptedAsk()
            elif "conversation.talk" in state["action"]:
                raise InterruptedTalk()

        if state["action"] and state["reached_end"] and ask and ask != state["ask"]:
            raise AskInCooldown()

        if state["action"] is None:
            state["action"] = action

        if state["story"] is None:
            state["story"] = story

        if state["ask"] is None:
            state["ask"] = ask

        # Build full translation key and translate
        result = translation_manager.translate(
            f"{state['action']}.{state['story']}.{state['index']}",
            lang=ctx.interaction.locale
        )

        next_result = translation_manager.translate(
            f"{state['action']}.{state['story']}.{state['index'] + 1}",
            lang=ctx.interaction.locale
        )

        if next_result == f"[{state['action']}.{state['story']}.{state['index'] + 1}]":
            state["reached_end"] = True

        # Advance index only if not at the end
        if not state["reached_end"]:
            state["index"] += 1

        state["last_time"] = now

        if state["reached_end"]:
            # Finished introduction
            if "conversation.introduction" in state["action"]:
                if not user.statistics.met_boomy:
                    user.statistics.met_boomy = True
                    self.storage_room_cog.user_database.update(user.id, user)

            match state["action"] + "." + state["story"]:
                case "conversation.talk.ask.about_boomy.intro":
                    if not user.statistics.knows_boomy:
                        user.statistics.knows_boomy = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_cafe.intro":
                    if not user.statistics.knows_cafe:
                        user.statistics.knows_cafe = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_berry.intro":
                    if not user.statistics.knows_berry:
                        user.statistics.knows_berry = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_jax.intro":
                    if not user.statistics.knows_jax:
                        user.statistics.knows_jax = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_dad.intro":
                    if not user.statistics.knows_dad:
                        user.statistics.knows_dad = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_mystery_console.intro":
                    if not user.statistics.knows_mystery_console:
                        user.statistics.knows_mystery_console = True
                        self.storage_room_cog.user_database.update(user.id, user)
                case "conversation.talk.ask.about_boomy_ears.intro":
                    if not user.statistics.knows_boomy_ears:
                        user.statistics.knows_boomy_ears = True
                        self.storage_room_cog.user_database.update(user.id, user)

        result += "\n⮟" if not state["reached_end"] else ""

        # No message yet
        if state["message"] is None:
            response = await ctx.respond(
                content=result,
                wait=True
            )

            state["message"] = response
        # Message is in another channel
        elif state["message"].channel.id != ctx.channel.id:
            await state["message"].delete()

            response = await ctx.respond(
                content=result,
                wait=True
            )

            state["message"] = response
        else:
            response = await state["message"].edit(
                content=result
            )

            await ctx.respond(
                content="​",
                ephemeral=True,
                delete_after=0
            )

        data["response_id"] = response.id

    @talk.error
    async def on_talk_error(self, ctx: discord.ApplicationContext, exception):
        data: dict[str, Any] = {
            "channel_id": ctx.channel.id,
            "response_id": None,
            "locale": ctx.interaction.locale,
            "error": None,
            "cooldown": None
        }

        match exception.original:
            case AskBeforeIntroduction():
                data["error"] = "AskBeforeIntroduction"
            case AskInCooldown():
                data["error"] = "AskInCooldown"
            case InterruptedIntroduction():
                data["error"] = "InterruptedIntroduction"
            case InterruptedTalk():
                data["error"] = "InterruptedTalk"
            case InterruptedAsk():
                data["error"] = "InterruptedAsk"
            case _:
                data["error"] = "Exception"
                await self.maintenance_room_cog.handle_exception()

        match data["error"]:
            case "AskBeforeIntroduction":
                message = "response.boomy.talk.fail_ask_before_intro"
            case "InterruptedIntroduction":
                message = "response.boomy.talk.fail_interrupted_intro"
            case "InterruptedTalk":
                message = "response.boomy.talk.fail_interrupted_talk"
            case "InterruptedAsk":
                message = "response.boomy.talk.fail_interrupted_ask"
            case _:
                message = None

        if message is not None:
            match ctx.author.id:
                case Celebrity.Zark.value:
                    message += ".zark"
                case Celebrity.Amethyst.value:
                    message += ".amethyst"

            response = await self.respond_error(
                interaction=ctx.interaction,
                message=message,
                lang=ctx.interaction.locale
            )

            data["response_id"] = response.id
            return

        match data["error"]:
            case "AskInCooldown":
                message = "response.boomy.talk.fail_ask_cooldown"
            case _:
                message = None

        if message is not None:
            now = time.time()

            if ctx.author.id not in self.conversations:
                self.conversations[ctx.author.id] = {
                    "action": None,
                    "story": None,
                    "ask": None,
                    "message": None,
                    "index": 1,
                    "reached_end": False,
                    "interrupted": False,
                    "last_time": now
                }

            state = self.conversations[ctx.author.id]

            cooldown = 10 * 60

            data["cooldown"] = (now - state["last_time"]) - cooldown

            response = await self.respond_error(
                interaction=ctx.interaction,
                message=message,
                lang=ctx.interaction.locale,
                count=data["cooldown"],
                cooldown=data["cooldown"]
            )

            data["response_id"] = response.id
            return

        response = await self.respond_error(
            interaction=ctx.interaction,
            message="response.boomy.talk.fail_unknown",
            lang=ctx.interaction.locale
        )

        data["response_id"] = response.id

    async def prank(self, ctx):
        """
        (Hidden command for mods) Makes Boomy load a fake/glitchy game to surprise someone.
        :param ctx:
        :return:
        """
        raise NotImplemented()

    def __find_branch(self, text: str, keywords: dict[str, str | dict]) -> str | None:
        """
        Recursively search for the first matching keyword sequence.
        - If a keyword maps to a dict: keep searching inside that dict.
        - If a keyword maps to a string: return it.
        """
        for keyword, branch in keywords.items():
            pattern = r"\b(" + keyword + r")\b"
            match = re.search(pattern, text)
            if not match:
                continue

            if isinstance(branch, dict):
                # continue searching in the substring after this match
                next_text = text[match.end():]
                result = self.__find_branch(next_text, branch)
                if result:
                    return result
            elif isinstance(branch, str):
                return branch

        return None

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
    bot.add_cog(Boomy(bot))
