from pprint import pprint
from utils.database_types import guild_data


def xp_to_levelup(lvl, xp=0):
    lvl -= 1
    return 5 * (lvl**2) + (50 * lvl) + 100 - xp


def total_xp_for_level(lvl, current_total_xp):
    total_xp = 0

    for level in range(0, lvl):
        total_xp += xp_to_levelup(level, 0)

    return total_xp - current_total_xp


def generate_level_table(max_level):
    level_table = {}
    total_xp = 0

    last_xp = 0

    for level in range(0, max_level + 1):
        xp_for_levelup = xp_to_levelup(level, 0)

        level_table.update({str(level): {"total_xp": total_xp}})

        if level > 0:
            level_table[str(level - 1)]["xp_for_levelup"] = last_xp

        total_xp += xp_for_levelup
        last_xp = xp_for_levelup

    return level_table


# print(total_xp_for_level(4, 0))


def reconcicle(base: dict, current: dict):
    data = {**base, **current}

    for key in data:
        value = data[key]

        if isinstance(value, dict):
            data[key] = reconcicle(base[key], value)

    return data


base = guild_data(836495137651294258)
data = {
    "welcome_message": {
        "embed": {
            "color": None,
        },
    },
}

pprint(reconcicle(base, data))
