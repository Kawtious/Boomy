import os
from typing import Type

from PIL import Image, ImageEnhance, ImageDraw
from PIL.Image import Resampling
from pyboy.utils import WindowEvent
from vault.data.database.gameboy_cartridge import GameBoyCartridge
from vault.data.database.user import User
from vault.exceptions.invalid_frame_data import InvalidFrameData

from config import Config
from emulator.base_emulator import BaseEmulator
from emulator.game.gameboy_game_instance import GameBoyGameInstance
from emulator.game.gameboy_game_instance_manager import GameBoyGameInstanceManager


class GameBoyEmulator(BaseEmulator):
    def __init__(self):
        super().__init__()
        self.game_instance_manager: GameBoyGameInstanceManager = GameBoyGameInstanceManager()

    def start(
            self,
            cartridge: GameBoyCartridge,
            user: User | Type[User]
    ) -> tuple[GameBoyGameInstance, Image]:
        game_instance, player = self.game_instance_manager.get_game_instance(cartridge, user)

        if not cartridge.state:
            game_instance.restart()
        else:
            game_instance.load_state(cartridge.state)

        frame = game_instance.screenshot()

        if not frame:
            raise InvalidFrameData()

        enable_color, enable_border, border = self.__get_premium_features(cartridge)

        frame = self.__process_frame(
            frame=frame,
            cartridge=cartridge,
            game_instance=game_instance,
            enable_color=enable_color,
            enable_border=enable_border,
            border=border
        )

        return game_instance, frame

    def input(
            self,
            cartridge: GameBoyCartridge,
            user: User | Type[User],
            button: str = None
    ) -> tuple[GameBoyGameInstance, list[Image]]:
        game_instance, player = self.game_instance_manager.get_game_instance(cartridge, user)

        # Load save state or restart
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
                button = [WindowEvent.PRESS_ARROW_UP, WindowEvent.RELEASE_ARROW_UP]
            case "down":
                button = [WindowEvent.PRESS_ARROW_DOWN, WindowEvent.RELEASE_ARROW_DOWN]
            case "left":
                button = [WindowEvent.PRESS_ARROW_LEFT, WindowEvent.RELEASE_ARROW_LEFT]
            case "right":
                button = [WindowEvent.PRESS_ARROW_RIGHT, WindowEvent.RELEASE_ARROW_RIGHT]
            case "a":
                button = [WindowEvent.PRESS_BUTTON_A, WindowEvent.RELEASE_BUTTON_A]
            case "b":
                button = [WindowEvent.PRESS_BUTTON_B, WindowEvent.RELEASE_BUTTON_B]
            case "start":
                button = [WindowEvent.PRESS_BUTTON_START, WindowEvent.RELEASE_BUTTON_START]
            case "select":
                button = [WindowEvent.PRESS_BUTTON_SELECT, WindowEvent.RELEASE_BUTTON_SELECT]

        frames = game_instance.input(button, duration_frames)

        if not frames:
            raise InvalidFrameData()

        enable_color, enable_border, border = self.__get_premium_features(cartridge)

        frames = [
            self.__process_frame(
                frame=frame,
                cartridge=cartridge,
                game_instance=game_instance,
                enable_color=enable_color,
                enable_border=enable_border,
                border=border
            )
            for frame in frames
        ]

        # Save state
        cartridge.state = game_instance.save_state
        cartridge.play_time += len(frames)

        return game_instance, frames

    def __process_frame(
            self,
            frame: Image,
            cartridge: GameBoyCartridge,
            game_instance: GameBoyGameInstance,
            enable_color=False,
            enable_border=False,
            border: str = None
    ) -> Image:
        processed_frame: Image = frame.copy()

        if enable_border:
            border_frame = None

            try:
                border_path = cartridge.border

                if border:
                    border_path = border

                border_frame = Image.open(os.path.join(Config.ASSETS_DIR, border_path))
            except Exception:
                pass

            if border_frame:
                border_frame = border_frame.convert("RGBA")

                x1, y1 = 48, 40  # top-left corner
                x2, y2 = 209, 184  # bottom-right corner

                new_width = x2 - x1
                new_height = y2 - y1

                game_frame_resized = processed_frame.resize((new_width, new_height), resample=Resampling.NEAREST)

                border_frame.paste(game_frame_resized, (x1, y1), game_frame_resized)

                processed_frame = border_frame

        if not enable_color:
            processed_frame = processed_frame.convert("L")
        else:
            processed_frame = processed_frame.convert("RGBA")

        processed_frame = processed_frame.resize(
            tuple(dimension * 1 for dimension in processed_frame.size),
            resample=Resampling.NEAREST
        )

        processed_frame = self.__draw_controller(processed_frame, game_instance)

        return processed_frame

    @staticmethod
    def __draw_controller(frame: Image, game_instance: GameBoyGameInstance):
        processed_frame = frame.convert("RGBA").copy()
        draw = ImageDraw.Draw(processed_frame)

        w, h = processed_frame.size

        button_map = {
            "UP": WindowEvent.PRESS_ARROW_UP,
            "DOWN": WindowEvent.PRESS_ARROW_DOWN,
            "LEFT": WindowEvent.PRESS_ARROW_LEFT,
            "RIGHT": WindowEvent.PRESS_ARROW_RIGHT,
            "A": WindowEvent.PRESS_BUTTON_A,
            "B": WindowEvent.PRESS_BUTTON_B,
            "START": WindowEvent.PRESS_BUTTON_START,
            "SELECT": WindowEvent.PRESS_BUTTON_SELECT
        }

        # Read controller states from emulator
        controller_state = game_instance.inputs

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

        def render_controller(base_x: int, base_y: int):
            size = 6

            # D-pad
            draw_button(bool(button_map["UP"] in controller_state),
                        [base_x + size, base_y, base_x + 2 * size, base_y + size])
            draw_button(bool(button_map["DOWN"] in controller_state),
                        [base_x + size, base_y + 2 * size, base_x + 2 * size, base_y + 3 * size])
            draw_button(bool(button_map["LEFT"] in controller_state),
                        [base_x, base_y + size, base_x + size, base_y + 2 * size])
            draw_button(bool(button_map["RIGHT"] in controller_state),
                        [base_x + 2 * size, base_y + size, base_x + 3 * size, base_y + 2 * size])

            # Start & Select
            draw_button(bool(button_map["START"] in controller_state),
                        [base_x + 7 * size, base_y + size, base_x + 8 * size, base_y + 2 * size], "rect")
            draw_button(bool(button_map["SELECT"] in controller_state),
                        [base_x + 5 * size, base_y + size, base_x + 6 * size, base_y + 2 * size], "rect")

            # A & B
            draw_button(bool(button_map["A"] in controller_state),
                        [base_x + 12 * size, base_y + size, base_x + 13 * size, base_y + 2 * size], "ellipse")
            draw_button(bool(button_map["B"] in controller_state),
                        [base_x + 10 * size, base_y + size, base_x + 11 * size, base_y + 2 * size], "ellipse")

        margin = 10
        render_controller(margin, h - 20)  # P1 left

        return processed_frame

    @staticmethod
    def __fade_frames_to_gray(frames: list[Image]) -> list[Image]:
        faded_frames = frames.copy()

        last_frame = faded_frames[-1].convert("RGBA")
        num_fade_frames = 10  # You can increase for smoother fade

        # Convert last frame to grayscale separately
        gray_frame = last_frame.convert("L").convert("RGBA")

        # Generate fade frames from color to grayscale
        fade_frames = []

        for i in range(1, num_fade_frames + 1):
            alpha = i / num_fade_frames
            blended = Image.blend(last_frame, gray_frame, alpha)

            brightness_factor = 1.0 - (alpha * 0.3)  # Up to 30% darker
            enhancer = ImageEnhance.Brightness(blended)
            darkened = enhancer.enhance(brightness_factor)

            fade_frames.append(darkened)

        # Replace the last frame with a pause+fade effect
        # Keep the last full-color frame, then show the fade to gray
        faded_frames[-1] = last_frame
        faded_frames.extend(fade_frames)

        return faded_frames

    @staticmethod
    def __get_premium_features(cartridge: GameBoyCartridge):
        if not cartridge.user.premium:
            return False, False, cartridge.border

        enable_color = cartridge.user.gameboy_profile.enable_color
        enable_border = cartridge.user.gameboy_profile.enable_border
        border = os.path.join(str(cartridge.user.id), "gameboy", cartridge.title, cartridge.border)

        if enable_border and cartridge.user.gameboy_profile.custom_border:
            border = os.path.join(str(cartridge.user.id), "gameboy", cartridge.user.gameboy_profile.custom_border)

        return enable_color, enable_border, border
