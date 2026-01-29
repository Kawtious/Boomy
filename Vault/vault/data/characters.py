from enum import Enum
from typing import TypedDict


class Celebrity(Enum):
    Zark = 262113677900120065
    Amethyst = 276133054337122305
    Cafe = 1409013944634572991
    Boomy = 1398806152535474196
    Berry = -1
    Jax = -1


class Character(TypedDict):
    id: str
    username: str
    avatar_url: str
    pokemon: str | None


class Characters:
    Boomy = Character(
        id="boomy",
        username="Boomy",
        avatar_url="https://i.imgur.com/tSwxGh1.gif",
        pokemon="""
            Boomy @ Eviolite
            Ability: Game Glitch
            Tera Type: Dark
            EVs: 252 SpA / 4 SpD / 252 Spe
            Jolly Nature
            - Nasty Plot
            - Glitch Pulse
            - Dark Pulse
            - Substitute
        """
    )
