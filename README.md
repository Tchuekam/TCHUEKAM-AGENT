# TCHUEKAM — Autonomous Enterprise Intelligence Platform

```
================================================================================
████████╗ ██████╗██╗  ██╗██╗   ██╗███████╗██╗  ██╗ █████╗ ███╗   ███╗  ██████╗██╗     ██╗
╚══██╔══╝██╔════╝██║  ██║██║   ██║██╔════╝██║  ██║██╔══██╗████╗ ████║ ██╔════╝██║     ██║
   ██║   ██║     ███████║██║   ██║█████╗  ███████║███████║██╔████╔██║ ██║     ██║     ██║
   ██║   ██║     ██╔══██║██║   ██║██╔══╝  ██╔══██║██╔══██║██║╚██╔╝██║ ██║     ██║     ██║
   ██║   ╚██████╗██║  ██║╚██████╔╝███████╗██║  ██╗██║  ██║██║ ╚═╝ ██║ ╚██████╗███████╗██║
   ╚═╝    ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═════╝╚══════╝╚═╝
================================================================================
  [SOVEREIGN ENGINE CORE] [RELEASE: 6 JUIN 2026] [Cameroon Agentic Intelligence]
================================================================================
```

## 1. Product Positioning & Market Focus
**TCHUEKAM** (or Sovereign.OS) is the first autonomous agentic AI platform developed in Cameroon, engineered by **Giantect Empire** (Inventor: **TCHUEKAM Loic Rostand**). 

Unlike standard cloud-bound generalist assistants, TCHUEKAM is a B2B enterprise operating intelligence system designed for 100% offline, zero-cloud data residency. It protects local client secrets under strict legal compliance frameworks, making it the premier deployment choice for high-security environments, beginning with Law Firms (*Cabinets d'Avocats*) in Yaoundé and Douala.

---

## 2. The 5 Operational Pillars
TCHUEKAM compiles and executes five native corporate capabilities entirely on local host hardware:

```
+---------------------------------------------------------------------------------+
|                              SOVEREIGN CORE ENGINE                              |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  [Pillar 1: Smart Briefing]  -->  Summarizes email/WhatsApp threads into a      |
|                                   2-minute morning executive brief.             |
|                                                                                 |
|  [Pillar 2: Company Brain]   -->  Indexes historical files (contracts, invoices)|
|                                   into a local semantic QA database.            |
|                                                                                 |
|  [Pillar 3: PL Analytics]    -->  Queries local spreadsheets using plain        |
|                                   natural language (Python/Pandas execution).   |
|                                                                                 |
|  [Pillar 4: File Intel]      -->  Instant search across all local drives        |
|                                   indexed via SQLite FTS5 (<6ms resolution).    |
|                                                                                 |
|  [Pillar 5: Doc Ops Center]  -->  Cross-checks file inconsistencies, missing    |
|                                   signatures, and duplicate archives.           |
+---------------------------------------------------------------------------------+
```

---

## 3. Technology Stack & Workspace Structure
The codebase is structured into clean modular layers:
* `tchuekam-agent/app/`: The Python core processor running the main agent orchestration loop.
  * `tools/`: Atomic system controllers (database crawling, terminal execution, filesystem operations, memory graphs).
  * `agent/`: State models, prompt assembly scripts, and safety locks.
  * `skills/`: Specialist instruction modules for specific tasks.
* `TchuEkaM/`: Node.js Slack / chat gateway connector bridging the localized engine with enterprise messaging environments.
* `~/.tchuekam/` (or `$TCHUEKAM_HOME`): Secure, local metadata persistence vault holding custom SQLite indexes and session memories entirely offline.

---

## 4. Quick-Start Deployment (Core execution)
To initialize TCHUEKAM in a new local environment:

1. **Verify Python 3.11** and compile the virtual environment:
   ```powershell
   cd tchuekam-agent/app
   uv venv --python 3.11
   uv sync
   ```
2. **Setup your environment variables** (`.env`):
   ```env
   DEEPSEEK_API_KEY=sk-your-key-here
   ```
3. **Trigger Initial Background Drive Crawl**:
   ```powershell
   .\venv\Scripts\python.exe -c "import sys; sys.path.append('.'); from tools.tchuekam_indexer import run_background_index; run_background_index(['C:\\Users\\CLINIC\\Documents'])"
   ```
4. **Boot TCHUEKAM interactive console**:
   ```powershell
   .\venv\Scripts\python.exe cli.py
   ```

---

*Engineered by Giantect Empire. Strictly offline secured.*
