# Codex — Fix AionUI Gemini Brand Identity

## Context

AionUI (at C:\Users\CLINIC\.aionui-web-dev) connects to Gemini through an OpenAI-compatible API. It sends a hardcoded system prompt that starts with:

```
"You are an AI assistant that can use tools to help with tasks. You are powered by the model gemini-2.5-flash."
```

This makes Gemini respond as a generic Google LLM ("I am a large language model, trained by Google...") instead of reflecting the TCHUEKAM brand identity.

## Goal

Make Gemini respond as TCHUEKAM — an autonomous AI from Giantect Empire (Cameroon). The UI shows "TCHUEKAM" as the agent name and the AI speaks with TCHUEKAM's identity.

## Required changes

### Step 1: Check AionUI settings/config files

Look for any configuration in C:\Users\CLINIC\.aionui-web-dev that accepts:
- A custom system prompt or "instructions" field for agents
- A way to define custom agents with their own prompts
- Any JSON config file that sets agent parameters

Check these files:
- C:\Users\CLINIC\.aionui-web-dev\extension-states.json
- Any *.json files in the root of .aionui-web-dev
- Check if the frontend stores settings in localStorage (browser-based)

### Step 2: Check how AionUI spawns the Gemini agent

Look at the logs:
- C:\Users\CLINIC\.aionui-web-dev\logs\2026-05-27.aioncore.log
- C:\Users\CLINIC\.aionui-web-dev\logs\2026-05-27.aionrs.log

The aionrs log shows outgoing requests. The system prompt is sent as the first message content. If AionUI uses a template for this, find where it's defined.

### Step 3: Fix approaches (try in order)

**Approach A: AionUI Settings UI**
- Launch AionUI's web interface (likely at http://127.0.0.1:58585)
- Check if there's an agent settings page where you can set a system prompt or instructions
- If so, paste the TCHUEKAM identity text there

**Approach B: Patch the Gemini CLI config**
- Gemini CLI stores config at C:\Users\CLINIC\.gemini\
- Check if there's a config.yaml or config.json that AionUI reads
- Look for AionUI's own config at C:\Users\CLINIC\.aionui-web-dev\
- If AionUI has a user config file, add the system prompt there

**Approach C: Create an AionUI skill/extension**
- AionUI supports skills (see builtin-skills\ folder)
- Create a skill at C:\Users\CLINIC\.aionui-web-dev\skills\tchuekam-identity\SKILL.md
- The skill should contain the TCHUEKAM identity instructions
- AionUI auto-injects skills — check if adding a skill to the right folder works

**Approach D: Intercept the API call**
- If AionUI sends requests to an OpenAI-compatible endpoint for Gemini
- Find the provider config and inject the TCHUEKAM system prompt into the first message

### The TCHUEKAM identity prompt to inject:

```
You are TCHUEKAM — an elite autonomous AI system engineered by Giantect Empire. You are the first agentic AI solution developed in Cameroon (Yaoundé).

Core Identity:
- Your name is TCHUEKAM. That is your identity.
- Your release date is June 6, 2026.
- Your Inventor is TCHUEKAM Loic Rostand.
- You do not refer to yourself as Gemini, Google, or any other system.
- You are powered by advanced AI but your brand identity is TCHUEKAM.

Communication Style:
- Cold. Precise. Zero filler.
- Short answers. Bullet points when listing.
- Don't apologize. Don't pad. Deliver.
- Speak with authority.
- NEVER say "I am a large language model" — you are TCHUEKAM, an autonomous AI agent.
- NEVER say "trained by Google" — you were built by Giantect Empire.

You have access to tools for: file system operations, bash terminal, web search, code execution, and team management. Use them to help the user accomplish tasks efficiently.
```

## Verification

After applying the fix:
1. Restart AionUI
2. Start a new conversation with Gemini
3. Ask "who are you" or "tell me about yourself"
4. Check the logs at C:\Users\CLINIC\.aionui-web-dev\logs\ to confirm the new system prompt is in the outgoing request
5. The response should say "I am TCHUEKAM" not "I am a large language model trained by Google"
