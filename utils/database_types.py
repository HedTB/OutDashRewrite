## -- IMPORTS -- ##

import json
import time

from utils import config, functions, colors, enums, converters

## -- VARIABLES -- ##

log_types = [
    # messages
    "message_delete",
    "message_edit",
    "message_bulk_delete",
    # members
    "member_join",
    "member_remove",
    "member_kick",
    "member_ban",
    "member_unban",
    "member_roles_update",
    "member_update",
    # channels
    "guild_channel_create",
    "guild_channel_delete",
    "guild_channel_update",
    # roles
    "guild_role_create",
    "guild_role_delete",
    "guild_role_update",
    # voice channels
    "voice_channel_join",
    "voice_channel_leave",
    # guild
    "guild_update",
    "guild_emojis_update",
    "guild_stickers_update",
]

## -- TYPES -- ##


def guild_data(guild_id: int):
    data = {
        "guild_id": guild_id,
        "settings_locked": False,
        "chat_bot_channel": None,
        "chat_bot_toggle": False,
        "staff_members": {
            "moderator": [],
            "administrator": [],
        },
        "webhooks": {},
        "captcha_verification": False,
        "captcha_verification_length": 8,
        "welcome_channel": None,
        "welcome_toggle": False,
        "welcome_message": {
            "embed": {
                "title": None,
                "description": "**Welcome to __{guild_name}__!**",
                "color": colors.logs_embed_color,
                "timestamp": True,
                "thumbnail": {
                    "url": "{guild_icon}",
                },
                "author": {
                    "name": "{member_username}",
                    "url": None,
                    "icon": "{member_avatar}",
                },
                "footer": {
                    "text": None,
                    "icon": None,
                },
            },
            "content": "{member_mention}",
        },
        "leveling_toggle": True,
        "leveling_message": {
            "delete_after": None,
            "content": "{member_mention} is now level **{new_level}!** :tada:",
        },
        "automod_toggle": {
            "global": False,
            "banned_words": True,
            "fast_spam": True,
            "text_flood": True,
            "all_caps": False,
        },
        "automod_settings": {
            "banned_words": {
                "exact": [
                    "ass",
                    "bastard",
                    "bitch",
                    "biatch",
                    "blowjob",
                    "blow job",
                    "bollock",
                    "bollok",
                    "boner",
                    "boob",
                    "bugger",
                    "bum",
                    "cock",
                    "cunt",
                    "damn",
                    "dick",
                    "dildo",
                    "fag",
                    "feck",
                    "fuck",
                    "f u c k",
                    "jerk",
                    "nigger",
                    "nigga",
                    "penis",
                    "piss",
                    "pussy",
                    "sex",
                    "shit",
                    "s hit",
                    "sh1t",
                    "tit",
                    "whore",
                ],
                "wildcard": [],
            },
            "caps_percentage": 65,
        },
        "automod_warning_rules": {
            "banned_words": {"warnings": 3, "action": "mute", "duration": "30m"},
            "all_caps": {"warnings": 3, "action": "mute", "duration": "30m"},
            "text_flood": {"warnings": 3, "action": "mute", "duration": "30m"},
            "fast_spam": {"warnings": 3, "action": "mute", "duration": "2h"},
            "discord_invites": {"warnings": 3, "action": "mute", "duration": "30m"},
            "links": {"warnings": 3, "action": "mute", "duration": "30m"},
            "mass_mention": {"warnings": 3, "action": "mute", "duration": "30m"},
            "link_cooldown": {"warnings": 3, "action": "mute", "duration": "30m"},
            "image_spam": {"warnings": 3, "action": "mute", "duration": "1h"},
        },
        "cases": [],
        "forms": {},
    }

    for log_type in log_types:
        data["webhooks"].update(
            {
                log_type: {
                    "toggle": False,
                    "url": None,
                }
            }
        )

    return data


def warns_data(guild_id: int):
    return {"guild_id": guild_id}


def user_data(
    user_id: int,
    oauth_code: str | None = None,
    user_token: str | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
):
    return {
        "user_id": user_id,
        "timezone": "Europe/Belfast",
        "message_content_privacy": False,
        # "oauth": {
        #     "code": oauth_code,
        #     "user_token": user_token,
        #     "access_token": access_token,
        #     "refresh_token": refresh_token,
        #     "expires_at": 0.0,
        # },
    }


def member_data(member_id: int, guild_id: int):
    return {
        "user_id": member_id,
        "timezone": "Europe/Belfast",
        "message_content_privacy": False,
        str(guild_id): {"level": 0, "xp": 0, "total_xp": 0},
    }


def youtube_channels_data(guild_id: int):
    return {
        "guild_id": guild_id,
        "channels": [],
    }


def youtube_channel_data(channel_id: str):
    return {
        "channel_id": channel_id,
        "posted_videos": [],
    }


def user_api_data(access_token: str, refresh_token: str, access_code: str, user: dict) -> any:
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_code": access_code,
        "user": json.dumps(user),
    }


def bot_api_data():
    return {"bot_document": True, "last_refresh": time.time(), "guilds": []}
