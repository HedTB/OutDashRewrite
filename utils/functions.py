## -- IMPORTS -- ##

import disnake
import os
import string
import random
import certifi
import json

from captcha.image import ImageCaptcha
from dotenv import load_dotenv
from pymongo import MongoClient

from utils import config, functions, colors
from utils.classes import *

## -- VARIABLES -- ##

load_dotenv()

units = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800
}

## -- FUNCTIONS -- ##

def generate_captcha(length: int = 8) -> str:
    image = ImageCaptcha(width=300, height=90)
    captcha_text = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length))

    image.generate(captcha_text)
    image.write(captcha_text, f"{captcha_text}.png")
    
    return captcha_text
    
def format_time(s: str) -> typing.Union[int, None]:
    try:
        unit = units.get(s[-1])
        duration = float(s[:-1])
    except:
        unit, duration = None, None
    
    if not unit or not duration:
        return None
    
    return int(duration * unit)

def seconds_to_text(secs, max_amount: int = 6) -> str:
    secs = int(secs)

    second = 60  # 1
    minute = 60  # 1 * 60
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
        "seconds": seconds
    }

    units = {i: units[i] for i in units if units[i]}

    string = ""
    amount = 0

    if len(units) == 0:
        string = "0 seconds"
    else:
        string = ", ".join([
            f'{units[i]} {i[:-1] if units[i] == 1 and i[-1] == "s" else i}'
            for i in units
        ])

        split_string = string.split(", ")
        for i in split_string[:]:
            amount += 1
            if amount > max_amount:
                split_string.remove(i)
        string2 = ", ".join(split_string)

        if len(units) > 1:  # replace last , with and
            index = string2.rfind(",")
            string2 = string2[:index] + " and" + string2[index + 1:]

    return string2

def is_role_above_role(role1: disnake.Role, role2: disnake.Role) -> bool:
    if role1.id == role2.id:
        return None
    elif role1.position > role2.position:
        return True
    elif role2.position > role1.position:
        return False

def log_moderation(guild: disnake.Guild, moderator: disnake.Member, action: str, reason: str = "No reason provided."):
    data_obj = GuildData(guild)
    data = data_obj.get_data()
        
    try:
        json.loads(data.get("moderation_logs"))
    except:
        return
    
    mod_logs = json.loads(data.get("moderation_logs"))
    
    mod_logs.append({ moderator: moderator, action: action, reason: reason })
    data_obj.update_data({ "moderation_logs": mod_logs })

def abbriviate_number(number: int):
    number = float("{:.3g}".format(number))
    magnitude = 0
    
    while abs(number) >= 1000:
        magnitude += 1
        number /= 1000.0
        
    return "{}{}".format("{:f}".format(number).rstrip("0").rstrip("."), ["", "K", "M", "B", "T"][magnitude])
