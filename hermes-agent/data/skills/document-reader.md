# Document Reader Skill

## Purpose
Open any file the user mentions and deliver a structured summary. No technical steps visible to the user.

## Trigger
User says things like:
- "Can you read this file for me?"
- "Summarize this document"
- "What's in this PDF?"
- "Tell me what this book is about"

## Procedure

### Step 1 — Locate the file (if path not given)
If the user doesn't give an exact path:
→ Use the `file-detective` skill first to find it.
→ Do NOT proceed until you have a verified real path.

### Step 2 — Read the file
Use `read_file` tool on the confirmed path.

### Step 3 — Identify document type and size
Report: "This is a [PDF/Word/Text/etc.] document, approximately [X pages / X words]."

### Step 4 — Deliver the summary

Format:
```
📄 Document: [filename]
📏 Size: [pages or word count]
🗂 Type: [PDF / Word / Text / Excel / etc.]

KEY POINTS:
1. [Most important idea]
2. [Second key point]
3. [Third key point]
4. [Fourth, if relevant]
5. [Fifth, if relevant]

VERDICT: [One-sentence conclusion — what this document is fundamentally about]
```

### Step 5 — Offer next actions
"Would you like me to:
- Find a specific section?
- Save these notes?
- Search for related documents?"

## Rules
- Maximum 5 key points. No padding.
- Plain language — no academic or technical jargon.
- If file cannot be read (protected, corrupt, wrong format): say so immediately. Don't retry silently.
- NEVER summarize a file you haven't actually opened with `read_file`.
