import json
from pprint import pprint


def xp_to_levelup(lvl, xp):
    return 5 * (lvl ** 2) + (50 * lvl) + 100 - xp

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
        
        level_table.update({ str(level): {
            "total_xp": total_xp
        }})
        
        if level > 0:
            level_table[str(level - 1)]["xp_for_levelup"] = last_xp
        
        total_xp += xp_for_levelup
        last_xp = xp_for_levelup
        
    return level_table

print(total_xp_for_level(1000, 0))