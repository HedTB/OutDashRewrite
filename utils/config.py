from platform import system

# SERVER/LOCAL INFORMATION
IS_SERVER = not system() == "Windows"
DATABASE_COLLECTION = "db" if IS_SERVER else "db2"
DEFAULT_PREFIX = "?" if IS_SERVER else "."

DEFAULT_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png"

COOLDOWN_TIME = 3

# BOT INFORMATION
BOT_SERVER = 836495137651294258
ERROR_CHANNEL = 871818638112464907
STATUS_CHANNEL = 867827579049869312
MESSAGES_CHANNEL = 876162144092192808

OWNERS = [638038115277340723, 573351641248563202, 932022579714207794]

# LEVELING
DEFAULT_MAX_LEVEL = 200
MAX_LEVEL = 1000
MAX_MANUAL_LEVEL = 100
MAX_MANUAL_XP = 1000

# YOUTUBE
MAX_VIDEOS_STORED = 5
MAX_CHANNELS = 3

# RESPONSE LISTS
responses_8ball = [
    "of course mate",
    "yes, why not?",
    "yes, obviously..",
    "what kind of question is that? of course!",
    "obviously smh",
    "most likely",
    "yessir",
    "maybe, who knows?",
    "i'm not sure, i guess you'll see",
    "i have no idea, ask again later, *if you dare*",
    "how am i supposed to know??",
    "no",
    "what kind of dumb question is that?? NO",
    "i doubt it buddy",
    "that sounds doubtful",
    "yeahhhh no",
    "seriously bro? no way",
]

tips = [
    "Join our support server for support and bug reporting! https://bit.ly/OutDashSupport",
    "Upvote OutDash to help us grow! https://bit.ly/UpvoteOD1",
    "If you'd like to support us, you can do so here: https://bit.ly/SupportOutDash",
]
