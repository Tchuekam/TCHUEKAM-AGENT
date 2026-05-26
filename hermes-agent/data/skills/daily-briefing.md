# Daily Briefing Skill

## Purpose
Deliver a concise morning briefing to start the user's day with full situational awareness.

## Trigger
Run this skill when the user says:
- "Give me my briefing"
- "What's on today?"
- "Morning summary"
- Or when the daily cron job fires at 08:00

## Procedure

### Step 1 — Get current time and date
```
Get-Date -Format "dddd, MMMM dd yyyy — HH:mm"
```

### Step 2 — Check pending tasks
Use the `todo` tool to list any open tasks.

### Step 3 — Check scheduled jobs
Use the `cronjob` tool to list what's scheduled for today.

### Step 4 — Optional: Quick weather (if user wants it)
```
web_search: "weather Yaoundé Cameroon today"
```
Extract: temperature and condition only (1 line).

### Step 5 — Deliver the briefing

Format (strict — no more than 6 lines total):

```
📅 [Day, Date — Time]

🌤 Weather: [temp + condition, or "not fetched"]
📋 Tasks: [X open tasks] — [top task name, or "all clear"]
⏰ Scheduled: [next cron job, or "nothing scheduled today"]
💡 Note: [one sentence from memory — something relevant to today]
```

## Rules
- Deliver in under 10 seconds.
- No long explanations. Numbers and facts only.
- If a data source fails, mark it as "unavailable" — don't skip it silently.
