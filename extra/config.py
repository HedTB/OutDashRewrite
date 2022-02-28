from platform import system

## -- NORMAL VALUES -- ##

is_server = False if system() == "Windows" else True
database_collection = "db" if is_server else "db2"
default_prefix = "?" if is_server else "."

embed_color = 0xd4d4d4
success_embed_color = 0x2ecc71
error_embed_color = 0xFF0000
logs_embed_color = 0x4286f4
logs_delete_embed_color = 0xdd5e53
logs_add_embed_color = 0x53ddad

cooldown_time = 3

bot_server = 836495137651294258
error_channel = 871818638112464907
status_channel = 867827579049869312
messages_channel = 876162144092192808

yes = "<:yes:872843660314685440>"
no = "<:no:872843057110867978>"
loading = "<a:loading:913452981070987285>"
partner = "<:partner:868630493078388746>"
server = "<:server:868630493107748885>"
upvote = "<:upvote:868630493086777394>"
work = "<:work:868630493309071381>"
info = "<:info:920728715011457034>"
moderator = "<:moderator:920732917901176832>"
toggleon = "<a:toggleon:920734948548305036>"
toggleoff = "<a:toggleoff:920734947692654592>"
offline = "<:offline:921402275900063774>"
online = "<:online:868630492843487292>"


## -- LISTS -- ##

owners = [638038115277340723, 573351641248563202, 932022579714207794]

emojis = {
}

jokes = ["Heard about the new restaurant called Karma?\nThere's no menu: you get what you deserve.",
         "Why do melons have weddings?\nBecause they cantaloupe.",
         'Why do we tell actors to "break a leg"?\nBecause every play has a cast.',
          'What did the buffalo say to his son?\nBison.',
          'Theres a new game called Silent Tennis.\nIts like regular tennis, but without the racquet.',
          'After I went to the dentist, I went and recorded a gospel album. My mouth was still numb, so I was drooling the whole time.\nThe album is called Songs of Salivation',
           'The world tongue-twister champion just got arrested.\nI hear theyre gonna give him a really tough sentence.',
            'Look! A blind dinosaur!\nYou think hesaurus?',
             'My doctor told me Im going deaf.\nThe news was hard for me to hear.',
              'I just memorized six pages of the dictionary.\nI learned next to nothing.',
               'My wife asked me today if I had seen the dog bowl.\nI said no because I didnt know he could.',
                'A weasel walks into the bar, the bartender says, hello weasel! What music would you like today?\nPop! Goes the weasel',]

responses_8ball = ["of course mate",
            "yes, why not?",
            "what are you thinking? YES OF COURSE",
            "what kinda of question is that? OF COURSE!",
            "obviously smh",
            "most likely",
            "yessir",
            "maybe, who knows?",
            "i'm not sure, i guess you'll see",
            "i have no idea, ask again later, *if you dare*",
            "how am i supposed to know??",
            "no",
            "what kinda of dumb question is that?? NO",
            "i doubt it buddy",
            "that sounds impossible",
            "yeahhhh no",
            "seriously bro? NO OF COURSE NOT"]

tips = ['Join our support server for support and bug reporting! https://bit.ly/OutDashSupport',
        'Upvote OutDash to help us grow! https://bit.ly/UpvoteOD1',
        "If you'd like to support us, you can do so here: https://bit.ly/SupportOutDash",
        "Upvote OutDash to help us grow! https://bit.ly/UpvoteOD2"]

hidden_commands = ["unloadcogs", "loadcogs", "reloadcogs"]