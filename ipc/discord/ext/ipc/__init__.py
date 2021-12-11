import collections

from ipc.discord.ext.ipc.client import Client
from ipc.discord.ext.ipc.server import Server
from ipc.discord.ext.ipc.errors import *


_VersionInfo = collections.namedtuple("_VersionInfo", "major minor micro release serial")

version = "2.1.1"
version_info = _VersionInfo(2, 1, 1, "final", 0)
