from enum import Enum


class Topics(Enum):
    Boomy = "About Boomy"
    Cafe = "About the café"
    Berry = "About Berry the Whimsicott"
    Jax = "About Jax the Rotom"
    Dad = "About Z'ark the Zoroark"
    MysteryConsole = "About the Mystery Console"
    BoomyEars = "About her ears?"

    def __str__(self):
        return str(self.value)
