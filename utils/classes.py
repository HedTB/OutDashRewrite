## -- IMPORTS -- ##

import disnake
import requests

from dotenv import load_dotenv

from utils.webhooks import *
from utils.database_types import *
from utils.data import *

from utils import config, functions, colors

## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##


class LoggingWebhook:
    def __init__(self, avatar: disnake.Asset, guild: disnake.Guild, log_type: str):
        self._data_obj = GuildData(guild)

        if not log_type in log_types:
            raise InvalidLogType

        webhook = self._data_obj.get_log_webhook(log_type)

        url = webhook["url"]
        toggle = webhook["toggle"]

        if not toggle or not url:
            raise InvalidWebhook
        elif toggle and not url:
            self._data_obj.update_log_webhook(
                log_type=log_type,
                data={"toggle": False, "url": None},
            )
            raise InvalidWebhook

        self._guild = guild
        self._log_type = log_type
        self._webhook = Webhook(url, avatar_url=str(avatar))

    def add_embeds(self, embeds: list[disnake.Embed]) -> None:
        for embed in embeds:
            self._webhook.add_embed(embed)

    def add_embed(self, embed: disnake.Embed):
        self._webhook.add_embed(embed)

    def post(self) -> requests.Response | None:
        data_obj = GuildData(self._guild)
        data = data_obj.get_data()

        try:
            return self._webhook.post()
        except InvalidWebhook:
            data["webhooks"][self._log_type]["toggle"] = False
            data_obj.update_data(data)
