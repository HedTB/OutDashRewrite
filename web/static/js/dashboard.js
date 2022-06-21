const guildCountElement = document.getElementById("guild-count");

let guilds = undefined;

function sleep(seconds) {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

async function updateBotData() {
  while (true) {
    await fetch("/dev/get-bot-data")
      .then((response) => response.json())
      .then((json) => {
        if (json["message"]) {
          location.href = "/login";
        } else {
          let responseGuilds = json["guilds"];
          let guildCount = json["guild_count"];

          guilds = responseGuilds;
          guildCountElement.innerText =
            "OutDash is in " + guildCount.toString() + " guilds";
        }
      });

    await sleep(15);
  }
}

updateBotData();
