import time

from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.user import User
from vault.exceptions.unauthorized_joypad_access import UnauthorizedJoypadAccess

from emulator.game.base_game_instance_manager import BaseGameInstanceManager
from emulator.game.gameboy_game_instance import GameBoyGameInstance


class GameBoyGameInstanceManager(BaseGameInstanceManager):
    def __init__(self):
        super().__init__()
        self.instances: dict[GameBoyCartridge, tuple[GameBoyGameInstance, list[int]]] = {}

    def get_game_instance(self, cartridge: GameBoyCartridge, user: User) -> tuple[GameBoyGameInstance, int]:
        # Update last used time
        self.last_used[cartridge] = time.time()

        # Use cached instance if available
        if cartridge in self.instances:
            instance, users = self.instances[cartridge]

            try:
                return instance, users.index(user.id)
            except ValueError:
                raise UnauthorizedJoypadAccess()

        # Otherwise create a new one
        instance = GameBoyGameInstance(cartridge)
        self.instances[cartridge] = (instance, [user.id])
        return instance, 0
