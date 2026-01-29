from typing import Type

import cynes
from PIL import Image, ImageDraw
from vault.data.database.nes_cartridge import NESCartridge
from vault.data.database.user import User
from vault.exceptions.invalid_frame_data import InvalidFrameData

from emulator.base_emulator import BaseEmulator
from emulator.game.nes_game_instance import NESGameInstance
from emulator.game.nes_game_instance_manager import NESGameInstanceManager


class NESEmulator(BaseEmulator):
    def __init__(self):
        super().__init__()
        self.game_instance_manager: NESGameInstanceManager = NESGameInstanceManager()

    def start(
            self,
            cartridge: NESCartridge,
            user: User | Type[User]
    ) -> tuple[NESGameInstance, Image]:
        game_instance, player = self.game_instance_manager.get_game_instance(cartridge, user)

        if not cartridge.state:
            game_instance.restart()
        else:
            game_instance.load_state(cartridge.state)

        frame = game_instance.screenshot()

        if not frame:
            raise InvalidFrameData()

        frame = self.__process_frame(frame=frame, game_instance=game_instance)

        return game_instance, frame

    def input(
            self,
            cartridge: NESCartridge,
            user: User | Type[User],
            button=None
    ) -> tuple[NESGameInstance, list[Image]]:
        game_instance, player = self.game_instance_manager.get_game_instance(cartridge, user)

        if not cartridge.state:
            game_instance.restart()
        else:
            game_instance.load_state(cartridge.state)

        game_instance.save_state_to_history(cartridge.state)

        duration_frames = 1

        if button is not None and isinstance(button, str):
            button = button.lower()
        else:
            button = None

        match button:
            case "frame 1":
                duration_frames = 1
                button = None
            case "frame 10":
                duration_frames = 10
                button = None
            case "frame 30":
                duration_frames = 30
                button = None
            case "frame 60":
                duration_frames = 60
                button = None
            case "up":
                button = cynes.NES_INPUT_UP
            case "down":
                button = cynes.NES_INPUT_DOWN
            case "left":
                button = cynes.NES_INPUT_LEFT
            case "right":
                button = cynes.NES_INPUT_RIGHT
            case "a":
                button = cynes.NES_INPUT_A
            case "b":
                button = cynes.NES_INPUT_B
            case "start":
                button = cynes.NES_INPUT_START
            case "select":
                button = cynes.NES_INPUT_SELECT

        if button is not None and isinstance(button, int):
            if player == 1:
                button = button << 8

        frames = game_instance.input(button, duration_frames)

        if not frames:
            raise InvalidFrameData()

        frames = [
            self.__process_frame(frame=frame, game_instance=game_instance)
            for frame in frames
        ]

        # Save state
        cartridge.state = game_instance.save_state
        cartridge.play_time += len(frames)

        return game_instance, frames

    @staticmethod
    def __process_frame(frame: Image, game_instance: NESGameInstance) -> Image:
        processed_frame = frame.convert("RGBA").copy()
        draw = ImageDraw.Draw(processed_frame)

        w, h = processed_frame.size

        # NES button bitmasks
        button_map = {
            "UP": cynes.NES_INPUT_UP,
            "DOWN": cynes.NES_INPUT_DOWN,
            "LEFT": cynes.NES_INPUT_LEFT,
            "RIGHT": cynes.NES_INPUT_RIGHT,
            "SELECT": cynes.NES_INPUT_SELECT,
            "START": cynes.NES_INPUT_START,
            "B": cynes.NES_INPUT_B,
            "A": cynes.NES_INPUT_A,
        }

        # Read controller states from emulator
        controller_state = game_instance.emulator.controller
        p1_state = controller_state & 0xFF
        p2_state = (controller_state >> 8) & 0xFF

        def draw_button(active: bool, coords, shape="rect"):
            # Always draw outline
            outline = (0, 100, 200, 180)  # faint blue outline

            if active:
                fill = (0, 150, 255, 220)  # solid blue highlight
            else:
                # fill = (0, 150, 255, 40)  # faint ghost fill
                fill = (0, 0, 0, 40)  # faint ghost fill

            if shape == "rect":
                draw.rectangle(coords, fill=fill, outline=outline, width=1)
            else:
                draw.ellipse(coords, fill=fill, outline=outline, width=1)

        def render_controller(state: int, base_x: int, base_y: int):
            size = 6

            # D-pad
            draw_button(bool(state & button_map["UP"]),
                        [base_x + size, base_y, base_x + 2 * size, base_y + size])
            draw_button(bool(state & button_map["DOWN"]),
                        [base_x + size, base_y + 2 * size, base_x + 2 * size, base_y + 3 * size])
            draw_button(bool(state & button_map["LEFT"]),
                        [base_x, base_y + size, base_x + size, base_y + 2 * size])
            draw_button(bool(state & button_map["RIGHT"]),
                        [base_x + 2 * size, base_y + size, base_x + 3 * size, base_y + 2 * size])

            # Select & Start
            draw_button(bool(state & button_map["SELECT"]),
                        [base_x + 5 * size, base_y + size, base_x + 6 * size, base_y + 2 * size], "rect")
            draw_button(bool(state & button_map["START"]),
                        [base_x + 7 * size, base_y + size, base_x + 8 * size, base_y + 2 * size], "rect")

            # B & A
            draw_button(bool(state & button_map["B"]),
                        [base_x + 10 * size, base_y + size, base_x + 11 * size, base_y + 2 * size], "ellipse")
            draw_button(bool(state & button_map["A"]),
                        [base_x + 12 * size, base_y + size, base_x + 13 * size, base_y + 2 * size], "ellipse")

        # Place Player 1 controller bottom-left, Player 2 bottom-right
        margin = 10
        render_controller(p1_state, margin, h - 20)  # P1 left
        render_controller(p2_state, w - 100, h - 20)  # P2 right

        return processed_frame
