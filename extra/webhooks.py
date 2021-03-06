import requests
import logging

logger = logging.getLogger("webhooks")

class InvalidWebhook(Exception):
    """Raised if the given webhook url is invalid."""
    pass

class Webhook:
    def __init__(self,
                 url=None,
                 content=None,
                 username="OutDash Logging",
                 avatar_url=None,
                 **kwargs
    ):
        self.url = url
        self.content = content
        self.username = username
        self.avatar_url = avatar_url
        self.tts = kwargs.get("tts", False)
        self.files = kwargs.get("files", dict())
        self.embeds = kwargs.get("embeds", [])
        self.proxies = kwargs.get("proxies")
        self.allowed_mentions = kwargs.get("allowed_mentions")
        self.timeout = kwargs.get("timeout")
        self.rate_limit_retry = kwargs.get("rate_limit_retry")

    @property
    def json(self):
        embeds = self.embeds
        self.embeds = []
        for embed in embeds:
            self.add_embed(embed, dict=True)
        data = {
            key: value
            for key, value in self.__dict__.items()
            if value and key not in {"url", "files", "filename"}
        }
        return data

    def add_embed(self, embed, dict=False):
        if dict == True:
            self.embeds.append(embed)
        else:
            embed_dict = embed.to_dict()
            self.embeds.append(embed_dict)

    def post(self, remove_embeds: bool = False):
        if not self.url.startswith("https://discord.com/api/webhooks/"):
            raise InvalidWebhook
            
        response = requests.post(url=self.url, json=self.json)

        try:
            response.raise_for_status()
        except Exception as error:
            logger.warn(error)