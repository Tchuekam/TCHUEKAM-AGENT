# File Detective Skill — Windows Edition

## Purpose
Find ANY file on this Windows computer. Always run real PowerShell commands. Never guess.

## This Machine
- OS: Windows 11
- Shell: PowerShell
- User: CLINIC
- Home: C:\Users\CLINIC
- Drives: C: and D:

## NEVER use Linux commands (find, ls, grep, cat). Use PowerShell only.

---

## Search Procedures

### 1. Quick Search — Common Personal Folders (Fastest, ~5 seconds)
```powershell
@("$env:USERPROFILE\Desktop", "$env:USERPROFILE\Downloads", "$env:USERPROFILE\Documents", "$env:USERPROFILE\OneDrive") | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem -Path $_ -Recurse -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "(?i)KEYWORD" } |
        Select-Object FullName
    }
}
```

### 2. Full Drive Search — C: only (~1-2 min)
```powershell
Get-ChildItem -Path "C:\Users\CLINIC" -Recurse -ErrorAction SilentlyContinue |
Where-Object { $_.Name -match "(?i)KEYWORD" } |
Select-Object FullName
```

### 3. Search by file type (PDF, EPUB, DOCX, etc.)
```powershell
Get-ChildItem -Path "C:\Users\CLINIC" -Recurse -Include "*.pdf","*.epub","*.docx","*.txt" -ErrorAction SilentlyContinue |
Where-Object { $_.Name -match "(?i)KEYWORD" } |
Select-Object FullName
```

### 4. List ALL folders on Desktop
```powershell
Get-ChildItem -Path "$env:USERPROFILE\Desktop" -Directory | Select-Object Name, FullName
```

### 5. List folder contents (excluding node_modules)
```powershell
Get-ChildItem -Path "FULL\PATH\HERE" -Exclude "node_modules" |
Select-Object Name, FullName, @{N="Size";E={if($_.PSIsContainer){"[DIR]"}else{"$([math]::Round($_.Length/1KB,1)) KB"}}}
```

### 6. Search inside files for text
```powershell
Select-String -Path "C:\Users\CLINIC\Documents\*" -Pattern "KEYWORD" -Recurse -ErrorAction SilentlyContinue
```

---

## Reporting Rules
- **Found**: List full paths exactly as returned by the command. No editing.
- **Not found**: Say "Not found." Period. No guesses.
- **Error**: Report the exact error message.
- **Always show the raw command output** — don't paraphrase results.

---

## After Finding a File
Ask: "Found it at [path]. Would you like me to open and summarize it?"
