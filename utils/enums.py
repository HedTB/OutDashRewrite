from enum import Enum


class Moderation(Enum):
    WARNING = 1
    KICK = 2
    BAN = 3
    MUTE = 4
    UNMUTE = 5
    SOFTBAN = 6