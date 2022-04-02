## -- IMPORTS -- ##

import json
import time

from utils import config

## -- VARIABLES -- ##

log_types = [
    # messages
    "message_delete", "message_edit", "message_bulk_delete",
    # members
    "member_join", "member_remove", "member_update", "member_ban", "member_unban", "user_update",
    # channels
    "guild_channel_create", "guild_channel_delete", "guild_channel_update",
    # roles
    "guild_role_create", "guild_role_delete", "guild_role_update",
    # voice channels
    "voice_channel_join", "voice_channel_leave",
    # guild
    "guild_update", "guild_emojis_update", "guild_stickers_update",
]

## -- TYPES -- ##

def guild_data(guild_id: int):
    data =  {
        "guild_id": guild_id,
        "prefix": "?",
        "settings_locked": False,

        "chat_bot_channel": None,
        "chat_bot_toggle": False,

        "webhooks": {},

        "captcha_verification": False,
        "captcha_verification_length": 8,

        "welcome_channel": None,
        "welcome_toggle": False,
        
        "welcome_message": {
            "embed": {
                "title": None,
                "description": "**Welcome to __{guild_name}__!**",
                
                "color": config.logs_embed_color,
                "timestamp": True,
                
                "thumbnail": {
                    "url": "{guild_icon}",
                },
                "author": {
                    "name": "{member_username}",
                    "url": None,
                    "icon": "{member_avatar}"
                },
                "footer": {
                    "text": None,
                    "icon": None,
                },
            },
            
            "content": "{member_mention}"
        },
        
        "leveling_toggle": True,
        "leveling_message": {
            "delete_after": None,
            "content": "{member_mention} is now level **{new_level}!** :tada:"
        }
    }
    
    for log_type in log_types:
        data["webhooks"].update({ log_type: {
            "toggle": False,
            "url": None,
        }})
    
    return data
    
def warns_data(guild_id: int):
    return {
        "guild_id": guild_id
    }
    
def user_data(user_id: int):
    return {
        "user_id": user_id,
        "timezone": "Europe/Belfast",
        "message_content_privacy": False,
    }

def member_data(member_id: int, guild_id: int):
    return {
        "user_id": member_id,
        "timezone": "Europe/Belfast",
        "message_content_privacy": False,
        
        str(guild_id): json.dumps({
            "level": 0,
            "xp": 0,
            "total_xp": 0
        })
    }
    
def user_api_data(access_token: str, refresh_token: str, access_code: str, user: dict):
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "access_code": access_code,
        
        "user": json.dumps(user)
    }
    
def bot_api_data():
    return {
        "bot_document": True,
        
        "last_refresh": time.time(),
        "guilds": {}
    }