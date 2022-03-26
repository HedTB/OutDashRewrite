## -- IMPORTS -- ##

import json
import time

from utils import config

## -- TYPES -- ##

def server_data(guild_id: int):
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
    
def warns_data(guild_id: int):
    return {
        "guild_id": str(guild_id)
    }
    
def user_data(user_id: int):
    return {
        "user_id": str(user_id),
        "timezone": "Europe/Belfast",
        "message_content_privacy": "false",
    }

def member_data(member_id: int, guild_id: int):
    return {
        "user_id": str(member_id),
        "timezone": "Europe/Belfast",
        "message_content_privacy": "false",
        
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
        "bot_document": "true",
        
        "last_refresh": time.time(),
        "guilds": {}
    }