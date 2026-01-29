import io
import os
import tempfile

from PIL import Image
from PIL.Image import Resampling
from pyboy import PyBoy
from vault.data.database.gameboy_cartridge import GameBoyCartridge

from config import Config
from emulator.game.base_game_instance import BaseGameInstance
from utils.frame_utils import FrameUtils


class GameBoyGameInstance(BaseGameInstance):
    def __init__(self, cartridge: GameBoyCartridge):
        super().__init__()

        with tempfile.NamedTemporaryFile(dir=os.path.join(Config.PROJECT_ROOT, "temp"), delete=False) as tmp_rom:
            tmp_rom.write(cartridge.rom)

        self.rom_path = tmp_rom.name

        self.emulator: PyBoy = PyBoy(
            window="null",
            gamerom=self.rom_path,
            sound_emulated=False,
            no_input=True,
            cgb=True
        )

        self.emulator.set_emulation_speed(0)

        self.__BOOT_ANIMATION: list[Image] = self.__gif_to_boot_animation(
            os.path.join(Config.ASSETS_DIR, "gameboy", cartridge.boot_animation)
        )

        self.__BOOT_SAVE_STATE: bytes = self.save_state

        self.inputs = []

    @staticmethod
    def __gif_to_boot_animation(gif_path: str) -> list[Image]:
        frames: list[Image] = []

        if gif_path is None or not os.path.isfile(gif_path):
            return frames

        try:
            custom_frames = FrameUtils.gif_to_frames(gif_path)
        except Exception:
            return frames

        # Settings
        boot_frames = 127
        frame_duration_multiplier = 12  # Show each frame for this many emulator frames

        # Resize all frames to 160x144
        scaled_frames = [
            frame.resize((160, 144), resample=Resampling.NEAREST)
            for frame in custom_frames
        ]

        # Minimum number of base frames needed before applying the multiplier
        required_base_frames = (boot_frames + frame_duration_multiplier - 1) // frame_duration_multiplier

        # If not enough frames, tile the list before applying multiplier
        if len(scaled_frames) < required_base_frames:
            repeats_needed = (required_base_frames + len(scaled_frames) - 1) // len(scaled_frames)
            scaled_frames = (scaled_frames * repeats_needed)[:required_base_frames]

        # Now repeat each frame according to the duration multiplier
        extended_frames = [
            frame for frame in scaled_frames
            for _ in range(frame_duration_multiplier)
        ]

        # Trim to exactly 72 frames
        final_frames = extended_frames[:boot_frames]

        # Add to output
        frames.extend(final_frames)

        return frames

    def __is_starting_from_boot(self):
        # Check PC is near the game's entry point
        pc = self.emulator.register_file.PC
        return pc == 0

    def max_players(self) -> int:
        return 1

    def restart(self):
        self.load_state(self.__BOOT_SAVE_STATE)

    def stop(self):
        self.emulator.stop(save=False)

        if os.path.isfile(self.rom_path) or os.path.islink(self.rom_path):
            os.unlink(self.rom_path)

    @property
    def save_state(self) -> bytes:
        with io.BytesIO() as save_state:
            self.emulator.save_state(save_state)
            save_state.seek(0)
            return save_state.read()

    def load_state(self, save_state: bytes):
        self.emulator.load_state(io.BytesIO(save_state))

    def screenshot(self) -> Image:
        return self.emulator.screen.image.copy()

    def input(self, button, duration_frames=10) -> list[Image]:
        frames: list[Image] = []

        frame_skip = 1  # 0 = Normal speed

        if self.__is_starting_from_boot():
            # Add to output
            if self.__BOOT_ANIMATION:
                frames.extend(self.__BOOT_ANIMATION)

            # Advance emulator by 127 ticks (same as number of boot frames)
            boot_frames = 127
            self.emulator.tick(boot_frames, render=False, sound=False)

        if button is not None:
            if button[0] in self.inputs:
                self.inputs.remove(button[0])
                self.inputs.append(button[1])
                controller_input = button[1]
            elif button[1] in self.inputs:
                self.inputs.remove(button[1])
                self.inputs.append(button[0])
                controller_input = button[0]
            else:
                self.inputs.append(button[0])
                controller_input = button[0]

            self.emulator.send_input(controller_input)

        for frame_count in range(duration_frames):
            self.emulator.tick(1 + frame_skip, render=True, sound=False)
            frames.append(self.screenshot())

        return frames
