import "dotenv/config";
import pkg, { LogLevel } from "@slack/bolt";
const { App } = pkg;

console.log("Initializing with tokens:", { 
  hasBotToken: !!process.env.SLACK_BOT_TOKEN, 
  hasAppToken: !!process.env.SLACK_APP_TOKEN 
});

const app = new App({
  token: process.env.SLACK_BOT_TOKEN,
  appToken: process.env.SLACK_APP_TOKEN,
  socketMode: true,
  logLevel: LogLevel.DEBUG,
});

// Listener for all messages
app.message(async ({ message, say }) => {
  // Check if it's a message from a user (not a bot)
  if (!("subtype" in message) || message.subtype === undefined) {
    // If it's a Direct Message (IM), respond to everything
    if (message.channel_type === "im") {
      await say(`Hermes received your signal: "${(message as any).text}". System is operational.`);
    } 
    // If it's in a channel, only respond if it contains 'hello' (to avoid spam)
    else if ((message as any).text?.toLowerCase().includes("hello")) {
      await say(`Hermes active in <#${message.channel}>. Signal received from <@${message.user}>.`);
    }
  }
});

// Listener for direct mentions
app.event("app_mention", async ({ event, say }) => {
  await say(`Hermes online. How can I assist, <@${event.user}>?`);
});

(async () => {
  try {
    await app.start();
    console.log("⚡️ Hermes system online (Socket Mode). Listening for signals.");
  } catch (error) {
    console.error("Critical failure during initialization:", error);
    process.exit(1);
  }
})();
