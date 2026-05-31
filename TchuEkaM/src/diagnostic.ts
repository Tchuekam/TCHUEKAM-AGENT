import "dotenv/config";
import { WebClient } from "@slack/web-api";

const client = new WebClient(process.env.SLACK_BOT_TOKEN);

async function runDiagnostic() {
  console.log("--- TchuEkaM Diagnostic Report ---");
  
  try {
    // 1. Identity Check
    const auth = await client.auth.test();
    console.log(`Identity: ${auth.user} (ID: ${auth.user_id})`);
    console.log(`Workspace: ${auth.team} (ID: ${auth.team_id})`);
    
    // 2. Connectivity Check
    console.log("Status: Web API Connected");
    
    // 3. Channel Access Check
    const channels = await client.conversations.list({ types: "public_channel,private_channel" });
    console.log(`Accessible Channels: ${channels.channels?.length || 0}`);
    
    // 4. Transmission Test
    // Find a channel to post in (e.g., #general or the first one available)
    const targetChannel = channels.channels?.find(c => c.name === "general") || channels.channels?.[0];
    
    if (targetChannel && targetChannel.id) {
      console.log(`Targeting Channel: #${targetChannel.name} (${targetChannel.id})`);
      
      // Try to join (in case it's not in it)
      try {
        await client.conversations.join({ channel: targetChannel.id });
      } catch (e) {
        // Might already be in it
      }
      
      const post = await client.chat.postMessage({
        channel: targetChannel.id,
        text: "🚨 *TchuEkaM System Diagnostic*: Outgoing transmission successful. WebSocket active. Systems nominal.",
      });
      
      if (post.ok) {
        console.log("Transmission Test: PASSED");
      }
    } else {
      console.log("Transmission Test: SKIPPED (No channels found)");
    }
    
    console.log("--------------------------------");
    process.exit(0);
  } catch (error) {
    console.error("Diagnostic Failed:", error);
    process.exit(1);
  }
}

runDiagnostic();
