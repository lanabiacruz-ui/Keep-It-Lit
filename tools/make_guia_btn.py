from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

UI = Path(__file__).resolve().parent.parent / "assets" / "maps" / "ui"

FILL = (62, 123, 198, 255)
INK = (32, 86, 148, 255)
TEXT = "Guía de teclas"

FONTS = (
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


def load_font(size):

    for path in FONTS:

        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    return ImageFont.load_default()


def make(src, dst):

    image = Image.open(UI / src).convert("RGBA")
    w, h = image.size

    draw = ImageDraw.Draw(image)

    draw.rectangle((14, 12, w - 15, h - 13), fill=FILL)

    size = 40

    while size > 12:

        font = load_font(size)
        box = draw.textbbox((0, 0), TEXT, font=font)

        if box[2] - box[0] <= w - 60:
            break

        size -= 1

    box = draw.textbbox((0, 0), TEXT, font=font)

    x = (w - (box[2] - box[0])) // 2 - box[0]
    y = (h - (box[3] - box[1])) // 2 - box[1]

    draw.text((x, y), TEXT, font=font, fill=INK)

    image.save(UI / dst)


if __name__ == "__main__":

    make("btn_controles.png", "btn_guia.png")
    make("btn_controles_hover.png", "btn_guia_hover.png")