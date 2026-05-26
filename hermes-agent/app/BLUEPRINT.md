# TCHUEKAM Code Assistant in Google One AI Pro

## BLUEPRINT: THE SOVEREIGN ENGINE

This document defines the architectural specification, operational pillars, and development blueprint for the **Sovereign Engine** (rebranded, enterprise-packaged edition of the Hermes Agent).

---

### 1. PRODUCT SPECIFICATION & MARKET POSITIONING
* **Product Name**: Sovereign Engine (or Sovereign.OS)
* **Market Focus**: High-security, local B2B enterprise automation.
* **Primary Target (Phase 1)**: Law Firms (*Cabinets d'Avocats*) in Douala and Yaoundé, Cameroon.
* **Key Differentiator**: **100% Offline / Zero-Cloud Data Residency**. Zero information leaves the physical server, protecting sensitive client secrets and intellectual property from foreign API storage while avoiding SaaS pricing models.

---

### 2. THE 5 OPERATIONAL PILLARS
The Sovereign Engine packages and delivers the following core enterprise capabilities:

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
|                                   indexed via SQLite FTS5 (<50ms resolution).   |
|                                                                                 |
|  [Pillar 5: Doc Ops Center]  -->  Cross-checks file inconsistencies, missing    |
|                                   signatures, and duplicate archives.           |
+---------------------------------------------------------------------------------+
```

---

### 3. TECHNICAL STACK
The Sovereign Engine is built directly on top of the **Hermes Agent** local runtime:
* **Core Agent Loop**: Python 3.11 with `uv` package management.
* **Local Inference**: `llama.cpp` running quantized GGUF models (e.g., Llama-3-8B-Instruct) on local CPUs or private GPU acceleration.
* **Database & Indexing**: SQLite 3 with FTS5 (Full-Text Search) extension.
* **Vector Embeddings**: Local ONNX sentence-transformer execution (`all-MiniLM-L6-v2`) for offline semantic indexing.
* **Automation Orchestration**: Native Cron scheduling, webhook listeners, and background task runners.
* **Primary Interfaces**: High-contrast local CLI, secure messaging channels (WhatsApp, Slack, Telegram).

---

### 4. CORE CODEBASE & FOLDER STRUCTURE
We extend the existing **Hermes Agent** codebase located at `D:\hermes-agent\app`:
* `tools/`: Python tool definitions (file_tools, terminal_tool, memory_tool).
* `agent/`: Orchestration loop, file safety systems, and state models.
* `skills/`: procedural memory capabilities (Obsidian, GitHub, web crawling).
* `gateway/`: Messaging platform connectors (Telegram, Slack, WhatsApp).
* `cron/`: Task automation schedules.

---

### 5. IMPLEMENTATION ORDER (PHASE 1)
To avoid the over-engineering resource trap, we execute a single-engine polymorphic build. Custom sector features (OHADA compliance, medical records integration) are treated as paid-for add-ons, leaving a single core codebase:

1. **Capability 1 (Pillar 4)**: High-speed SQLite FTS5 File Indexer (**Hour One Target**).
2. **Capability 2**: Local semantic embedding table using quantized ONNX models for true semantic search.
3. **Capability 3**: SQLite Persistent Memory Graph to preserve session context and avoid state-loss.
4. **Capability 4**: Hardened WhatsApp API local bridge for mobile gateway interactions.
5. **Capability 5**: Cron-based Morning Briefing execution engine.
