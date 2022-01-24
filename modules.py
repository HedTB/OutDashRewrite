import disnake
import datetime
import string
import random

import config

from captcha.image import ImageCaptcha


def list_to_string(list: list, separator: str) -> str:
    return f"{separator}".join(e for e in list)


def generate_captcha(length: int = 8) -> str:
    image = ImageCaptcha(width=300, height=90)
    captcha_text = ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length))

    image.generate(captcha_text)
    image.write(captcha_text, f"{captcha_text}.png")
    return captcha_text


async def get_db_data(guild_id: str) -> dict:
    return {
        "guild_id": str(guild_id),
        "prefix": "?",
        "settings_locked": "false",

        "chat_bot_channel": "None",
        "chat_bot_toggle": "false",

        "message_delete_logs_webhook": "None",
        "message_bulk_delete_logs_webhook": "None",
        "message_edit_logs_webhook": "None",
        "member_join_logs_webhook": "None",
        "member_remove_logs_webhook": "None",
        "user_update_logs_webhook": "None",
        "guild_channel_create_logs_webhook": "None",
        "guild_channel_delete_logs_webhook": "None",
        "guild_channel_update_logs_webhook": "None",

        "captcha_verification": "false",
        "captcha_verification_length": 8,
        
        "welcome_channel": "None",
        "welcome_toggle": "False",
        "welcome_embed_title": "None",
        "welcome_embed_description": "**Welcome to __{guild_name}__!**",
        "welcome_embed_author_name": "{member_username}",
        "welcome_embed_author_icon": "{member_icon}",
        "welcome_embed_footer_text": "None",
        "welcome_embed_footer_icon": "None",
        "welcome_embed_timestamp": "true",
        "welcome_embed_thumbnail": "{guild_icon}",
        "welcome_embed_color": config.logs_embed_color,
        "welcome_message_content": "{member_mention},",
    }


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
                return "InvalidInput"
        except Exception:
            return "InvalidInput"

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


def construct_webhook_embed(title: str = None,
                            description: str = None,
                            color: str = None,
                            timestamp: str = str(datetime.datetime.utcnow()),
                            author_name: str = None,
                            author_icon_url: str = None,
                            fields: dict = []) -> list:

    return [{
        "title": title,
        "description": description,
        "color": color,
        "timestamp": timestamp,
        "author": {
            "name": author_name,
            "icon_url": author_icon_url
        },
        "fields": fields
    }]
