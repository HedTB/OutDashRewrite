const guildCountElement = document.getElementById("guild-count");

function sleep(seconds) {
  return new Promise((resolve) => setTimeout(resolve, seconds * 1000));
}

async function updateBotData() {
  await fetch("/api/v2/guilds/bot/count")
    .then((response) => response.json())
    .then((json) => {
      if (json["message"]) {
        location.href = "/login";
      } else {
        let guildCount = json["guild_count"];

        console.log(`Guild count: ${guildCount}`)
        guildCountElement.innerText = `OutDash is in ${guildCount.toString()} guilds`;
      }
    }
    );
}

document.addEventListener("DOMContentLoaded", async () => {
  await updateBotData()

  setInterval(async () => {
    await updateBotData()
  }, 5000)
})