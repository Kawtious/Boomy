import io

from PIL import Image, ImageSequence, ImageDraw, ImageFont


class FrameUtils:
    @staticmethod
    def fps_to_ms(fps):
        return 1000 / fps

    @staticmethod
    def frame_to_bytes(frame) -> bytes:
        image_bytes_io = io.BytesIO()

        frame.save(
            image_bytes_io,
            format="PNG",
        )

        return image_bytes_io.getvalue()

    @staticmethod
    def frames_to_bytes(frames: list[Image]) -> bytes:
        gif_bytes_io = io.BytesIO()

        frames[0].save(
            gif_bytes_io,
            format="GIF",
            save_all=True,
            append_images=frames,
            loop=None,
            duration=FrameUtils.fps_to_ms(30)
        )

        return gif_bytes_io.getvalue()

    @staticmethod
    def gif_to_frames(gif_path: str) -> list[Image]:
        gif = Image.open(gif_path)

        return [
            frame.copy().convert("RGBA")
            for frame in ImageSequence.Iterator(gif)
        ]

    @staticmethod
    def text_to_image(text: str, font: str, font_size: int) -> Image:
        # Load the font
        font = ImageFont.truetype(font, font_size)

        # Calculate text size
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        text_width, text_height = draw.textsize(text, font=font)

        # Create image with size based on text
        image = Image.new('RGB', (text_width + 20, text_height + 20), color='white')
        draw = ImageDraw.Draw(image)

        # Draw the text
        draw.text((10, 10), text, font=font, fill='black')

        return image
