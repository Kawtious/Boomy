from enum import Enum


class Console(Enum):
    Pikapalette = "Pikapalette"
    PonytaEntertainmentSystem = "Ponyta Entertainment System"

    def __str__(self):
        return str(self.value)
