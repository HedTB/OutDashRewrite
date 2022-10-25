## -- IMPORTS -- ##

import disnake
import requests

from dotenv import load_dotenv

from utils.webhooks import InvalidWebhook, InvalidLogType, Webhook
from utils.database_types import log_types
from utils.data import GuildData


## -- VARIABLES -- ##

load_dotenv()

## -- FUNCTIONS -- ##


class LoggingWebhook:
    def __init__(self, avatar: disnake.Asset, guild: disnake.Guild, log_type: str):
        self._data_obj = GuildData(guild.id)

        if log_type not in log_types:
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
        data_obj = GuildData(self._guild.id)
        data = data_obj.get_data()

        try:
            return self._webhook.post()
        except InvalidWebhook:
            data["webhooks"][self._log_type]["toggle"] = False
            data_obj.update_data(data)
