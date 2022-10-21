import disnake

from disnake.ext import commands


def convert_time(inter: disnake.ApplicationCommandInteraction, input: str) -> int:
    try:
        time = round(int(input[:-1]))
        duration = input[-1].lower()

        if duration == "s":
            return time
        elif duration == "m":
            return time * 60
        elif duration == "h":
            return time * 60 * 60
        elif duration == "d":
            return time * 60 * 60 * 24
        elif duration == "y":
            return time * 60 * 60 * 24 * 365
        else:
            return int(input)
    except Exception:
        return None
