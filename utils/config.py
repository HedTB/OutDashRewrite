from platform import system

# SERVER/LOCAL INFORMATION
IS_SERVER = system() != "Windows"
DATABASE_COLLECTION = "db" if IS_SERVER else "db2"

DEFAULT_AVATAR_URL = "https://cdn.discordapp.com/embed/avatars/0.png"
COOLDOWN_TIME = 3

# BOT INFORMATION
CLIENT_ID = 836494578135072778 if IS_SERVER else 844937957185159198
PERMISSIONS = 1644972474367

BOT_SERVER = 836495137651294258
ERROR_CHANNEL = 871818638112464907
STATUS_CHANNEL = 867827579049869312
MESSAGES_CHANNEL = 876162144092192808

OWNERS = [638038115277340723, 573351641248563202]

INVITE_URL = (
    "https://discord.com/api/oauth2/authorize"
    f"?client_id={CLIENT_ID}&permissions={PERMISSIONS}&scope=bot%20applications.commands"
)

# API
SERVER_URL = "https://outdash.ga" if not IS_SERVER else "https://outdash-beta2.herokuapp.com"
REDIRECT_URI = SERVER_URL + "/callback"

# LEVELING
DEFAULT_MAX_LEVEL = 200
MAX_LEVEL = 1000
MAX_MANUAL_LEVEL = 100
MAX_MANUAL_XP = 1000

# YOUTUBE
MAX_VIDEOS_STORED = 5
MAX_CHANNELS = 3

# RESPONSE LISTS
RESPONSES_8BALL = [
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
    "i doubt it buddy",
    "that sounds doubtful",
    "yeahhhh no",
    "seriously bro? no way",
]

TIPS = [
    "Join our support server for support and bug reporting! https://bit.ly/OutDashSupport",
    "Upvote OutDash to help us grow! https://bit.ly/UpvoteOD1",
    "If you'd like to support us, you can do so here: https://bit.ly/SupportOutDash",
]
