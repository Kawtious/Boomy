import io
from typing import re

import discord
from discord import Message


def image_to_embed(image_bytes):
    file = discord.File(
        fp=io.BytesIO(image_bytes),
        filename="game.png"
    )

    embed = discord.Embed()
    embed.set_image(url="attachment://game.png")

    return file, embed


def gif_to_embed(gif_bytes):
    file = discord.File(
        fp=io.BytesIO(gif_bytes),
        filename="game.gif"
    )

    embed = discord.Embed()
    embed.set_image(url="attachment://game.gif")

    return file, embed


async def get_first_mention(message: Message):
    user_mention_regex = r"<@!?(\d+)>"
    role_mention_regex = r"<@&(\d+)>"

    # Search for the first user mention
    user_match = re.search(user_mention_regex, message.content)

    # If no user mention is found, check for a role mention
    if user_match:
        user_id = user_match.group(1)
        user = await message.guild.fetch_member(user_id)
        return user

    # If no user mention is found, check for a role mention
    role_match = re.search(role_mention_regex, message.content)
    if role_match:
        role_id = role_match.group(1)
        role = message.guild.get_role(int(role_id))
        return role

    return None
