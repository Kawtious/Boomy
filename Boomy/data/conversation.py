from typing import TypedDict

from discord import Message


class Conversation(TypedDict):
    action: str | None
    story: str | None
    ask: str | None
    message: Message | None
    index: int
    reached_end: bool
    last_time: float
