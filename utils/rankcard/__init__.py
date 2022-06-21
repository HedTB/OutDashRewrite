import requests
import os

from PIL import Image, ImageDraw, ImageFont
from math import *
from io import BytesIO

## -- VARIABLES -- ##


def _get_file_path(file_name: str):
    return os.path.join(os.path.dirname(__file__), "assets", file_name)


card_background = _get_file_path("card.png")
statuses = {
    "online": _get_file_path("online.png"),
    "dnd": _get_file_path("dnd.png"),
    "idle": _get_file_path("idle.png"),
    "offline": _get_file_path("offline.png"),
    "streaming": _get_file_path("streaming.png"),
}

## -- FUNCTIONS -- ##


def _abbreviate_number(number):
    endings = ["", "K", "M", "B", "T"]

    return endings[int(floor(log10(number)) / 3)]


def generate_card(
    username: str,
    avatar: str,
    status: str = "online",
    level: int = 1,
    current_xp: int = 0,
    next_level_xp: int = 100,
    rank: int = 1,
):
    card = Image.open(card_background).convert("RGBA")
    width, height = card.size

    x1, y1 = 0, 0
    x2, y2 = width, 0
    nh = ceil(width * 0.264444)

    if nh < height:
        y1 = (height / 2) - 119
        y2 = nh + y1

    card = card.crop((x1, y1, x2, y2)).resize((950, 275))
    status = Image.open(statuses[status]).convert("RGBA").resize((35, 35))

    avatar_bytes = BytesIO(requests.get(avatar).content)
    avatar = Image.open(avatar_bytes).convert("RGBA").resize((180, 180))
    avatar_holder = Image.new("RGBA", card.size, (255, 255, 255, 0))

    mask = Image.new("RGBA", avatar.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((29, 29, 180, 180), fill=(255, 25, 255, 255))

    source_sans_black = ImageFont.truetype(
        _get_file_path("SourceSansPro-Black.ttf"), 1.34
    )
    source_sans_bold = ImageFont.truetype(
        _get_file_path("SourceSansPro-Bold.ttf"), 0.93
    )
    fredoka_one = ImageFont.truetype(_get_file_path("FredokaOne-Regular.ttf"), 0.8)

    draw = ImageDraw.Draw(card)
    draw.text((287, 131), username[:5], (255, 255, 255, 255), source_sans_black)
    draw.text((434, 143), username[5:], (168, 168, 168, 255), source_sans_bold)

    draw.text(
        (0, 0),
        _abbreviate_number(current_xp) + " / " + _abbreviate_number(next_level_xp),
        (255, 255, 255, 255),
        fredoka_one,
    )

    blank = Image.new("RGBA", card.size, (255, 255, 255, 0))
    blank_draw = ImageDraw.Draw(blank)
    blank_draw.rounded_rectangle(())
