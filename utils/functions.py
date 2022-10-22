## -- IMPORTS -- ##

import re
import disnake
import string
import random

from captcha.image import ImageCaptcha
from dotenv import load_dotenv
from disnake.ext import commands

from utils import config, functions, colors, enums, converters
from utils.data import *

## -- VARIABLES -- ##

load_dotenv()

decimal_filter = re.compile(r"^\d*[.,]\d*$")

## -- FUNCTIONS -- ##


def convert_strings(iterable: dict | list):
    if isinstance(iterable, dict):
        for key, value in iterable.items():
            if isinstance(value, (dict, list)):
                iterable[key] = convert_strings(value)
            elif isinstance(value, str):
                iterable[key] = to_number(value, just_try=True)
    elif isinstance(iterable, list):
        for value in iterable:
            if isinstance(value, (dict, list)):
                iterable[iterable.index(value)] = convert_strings(value)
            elif isinstance(value, str):
                iterable[iterable.index(value)] = to_number(value, just_try=True)

    return iterable


def to_number(s: str, just_try=False):
    if decimal_filter.match(s):
        try:
            return float(s)
        except:
            if just_try:
                return s
            else:
                raise
    else:
        try:
            return int(s)
        except:
            if just_try:
                return s
            else:
                raise


def generate_captcha(length: int = 8) -> str:
    image = ImageCaptcha(width=300, height=90)
    captcha_text = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(length))

    image.generate(captcha_text)
    image.write(captcha_text, f"{captcha_text}.png")

    return captcha_text


def manipulate_time(time_str: str, return_type: str) -> int or str:
    if return_type == "seconds":
        try:
            time = int(time_str[:-1])
            duration = time_str[-1].lower()

            if duration == "s":
                return time
            elif duration == "m":
                return time * 60
            elif duration == "h":
                return time * 60 * 60
            elif duration == "d":
                return time * 60 * 60 * 24
            else:
                return None
        except Exception:
            return None

    elif return_type == "duration_type":
        duration = time_str[-1].lower()

        if duration == "s":
            return "seconds"
        elif duration == "m":
            return "minutes"
        elif duration == "h":
            return "hours"
        elif duration == "d":
            return "days"
        else:
            return "InvalidInput"

    elif return_type == "time":
        return time_str[:-1]


def seconds_to_text(secs, max_amount: int = 6) -> str:
    secs = int(secs)

    second = 60  # 1
    hour = 3600  # 1 * 60 * 60
    day = 86400  # 1 * 60 * 60 * 24
    month = 2629800  # 1 * 60 * 60 * 24 * 30
    year = 31556952  # 1 * 60 * 60 * 24 * 30 * 12

    years, remainder = divmod(secs, year)
    months, remainder = divmod(remainder, month)
    days, remainder = divmod(remainder, day)
    hours, remainder = divmod(remainder, hour)
    minutes, seconds = divmod(remainder, second)

    units = {
        "years": years,
        "months": months,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }

    units = {i: units[i] for i in units if units[i]}

    string = ""
    amount = 0

    if len(units) == 0:
        string = "0 seconds"
    else:
        string = ", ".join([f'{units[i]} {i[:-1] if units[i] == 1 and i[-1] == "s" else i}' for i in units])

        split_string = string.split(", ")
        for i in split_string[:]:
            amount += 1
            if amount > max_amount:
                split_string.remove(i)

        string = ", ".join(split_string)

        if len(units) > 1:  # replace last , with and
            index = string.rfind(",")
            string = string[:index] + " and" + string[index + 1 :]

    return string


def is_role_above_role(role1: disnake.Role, role2: disnake.Role) -> bool:
    if role1.id == role2.id:
        return None
    elif role1.position > role2.position:
        return True
    elif role2.position > role1.position:
        return False


async def get_or_make_invite(guild: disnake.Guild) -> str | None:
    invite = guild.vanity_url_code

    if invite:
        return invite

    try:
        for invite in await guild.invites():
            if invite.max_age == 0 and invite.max_uses == 0:
                return invite.url
    except:
        pass

    try:
        channel = guild.text_channels[0]
        invite_obj = await channel.create_invite(max_uses=1)
        invite = invite_obj.url
    except:
        invite = None

    return invite


def abbriviate_number(number: int):
    number = float("{:.3g}".format(number))
    magnitude = 0

    while abs(number) >= 1000:
        magnitude += 1
        number /= 1000.0

    return "{}{}".format(
        "{:f}".format(number).rstrip("0").rstrip("."),
        ["", "K", "M", "B", "T", "QA", "QI", "SX"][magnitude],
    )
