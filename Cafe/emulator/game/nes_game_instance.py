import os
import tempfile

from PIL import Image
from cynes import NES
from vault.data.database.nes_cartridge import NESCartridge

from config import Config
from emulator.game.base_game_instance import BaseGameInstance


class NESGameInstance(BaseGameInstance):
    def __init__(self, cartridge: NESCartridge):
        super().__init__()

        self.cartridge: NESCartridge = cartridge

        with tempfile.NamedTemporaryFile(dir=os.path.join(Config.PROJECT_ROOT, "temp"), delete=False) as tmp_rom:
            tmp_rom.write(cartridge.rom)

        self.rom_path = tmp_rom.name

        self.emulator: NES = NES(
            rom=self.rom_path
        )

        self.__BOOT_SAVE_STATE: bytes = self.save_state

    def max_players(self) -> int:
        return 2

    def restart(self):
        self.load_state(self.__BOOT_SAVE_STATE)

    def stop(self):
        if os.path.isfile(self.rom_path) or os.path.islink(self.rom_path):
            os.unlink(self.rom_path)

    @property
    def save_state(self) -> bytes:
        return self.emulator.save().tobytes()

    def load_state(self, save_state: bytes):
        # Does not work properly
        # self.emulator.load(np.frombuffer(save_state, dtype=np.uint8).copy())
        pass

    def screenshot(self) -> Image:
        return Image.fromarray(self.emulator.step())

    def input(self, button, duration_frames=10) -> list[Image]:
        frames: list[Image] = []

        frame_skip = 1  # 0 = Normal speed

        if button is not None:
            self.emulator.controller ^= button

        for frame_count in range(duration_frames):
            frame = self.emulator.step(1 + frame_skip)
            frames.append(Image.fromarray(frame))

        return frames
