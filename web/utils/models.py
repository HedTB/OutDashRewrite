## -- IMPORTS -- ##

import datetime
import typing

from pydantic import BaseModel

from utils import enums

## -- MODELS -- ##


class BotGuildData(BaseModel):
    id: int


class BotGuildCount(BaseModel):
    guild_count: int


class GuildData(BaseModel):
    id: int
    name: str
    icon: str
    owner: bool
    permissions: int


class SettingsLock(BaseModel):
    settings_locked: bool


class CaseData(BaseModel):
    id: int = None
    moderator: int
    offender: int
    action: enums.Moderation
    reason: str = "No reason provided."
    timestamp: datetime.datetime = None


class VoteData(BaseModel):
    bot: str
    user: str
    type: str
    isWeekend: typing.Union[bool, None]
    query: str


class Message(BaseModel):
    message: str
