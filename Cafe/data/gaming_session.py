from typing import TypedDict

from discord import Message
from discord.ui import View

from emulator.base_emulator import BaseEmulator


class GamingSession(TypedDict):
    emulator: BaseEmulator
    joypad: View
    message: Message | None
