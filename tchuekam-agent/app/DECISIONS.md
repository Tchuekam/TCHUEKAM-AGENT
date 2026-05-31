# TCHUEKAM Code Assistant in Google One AI Pro

## ARCHITECTURAL & STRATEGIC DECISIONS: SOVEREIGN ENGINE

This document records the exact rationales, context, and structural decisions made during the design of the Sovereign Engine.

---

### DECISION 1: Decoupled Single-Engine vs. Multi-Sector Codebases
* **Status**: **APPROVED**
* **Context**: We debated building distinct products for separate markets (`Sovereign.LAW`, `Sovereign.CLINIC`, `Sovereign.BUILD`).
* **Decision**: We rejected multi-base code builds. We will build **ONE polymorphic engine core**. 
* **Rationale**:
  * **Resource Trap Mitigation**: Designing five separate codebases before securing a single customer contract is over-engineering. It causes slow ship times and fragmented maintenance.
  * **Dynamic Context Adaptability**: Decoupling the Core Processing Layer from the Data Layer. The engine's intelligence is shaped dynamically by the *corpus of files it indexes*. When pointed at a legal directory, it reads and speaks legal terms. When pointed at patient profiles, it acts as a medical assistant.
  * **Paid Plugin Architecture**: High-margin custom workflows (OHADA synchronization, ERP data entry, patient record layouts) will be written as modular, contract-driven plugins paid separately by the enterprise.

---

### DECISION 2: 100% Offline / Local Execution Model
* **Status**: **APPROVED**
* **Context**: Choosing between hybrid-cloud API routing and fully local offline compute.
* **Decision**: The Sovereign Engine operates **100% locally** (or inside private enterprise VPCs). No data-sharing, no external cloud API routing.
* **Rationale**:
  * **Litigation Compliance**: Target law firms hold sensitive files protected under strict *secret professionnel*. They cannot legally upload this data to commercial third-party cloud engines.
  * **Economics**: Completely avoids token-limit taxes, API call limits, and recurring SaaS billing friction for the client, allowing us to charge premium, one-off deployment fees and monthly maintenance retainers.

---

### DECISION 3: Cabinet d'Avocats (Law Firms) as Phase 1 Launch Market
* **Status**: **APPROVED**
* **Context**: Selecting the primary commercial entry sector from 5 candidate markets.
* **Decision**: First commercial campaign targets **Cabinets d'Avocats in Douala and Yaoundé, Cameroon**.
* **Rationale**:
  * **High Pain Profile**: Lawyers spend up to 15 hours a week searching through fragmented Windows directories and scanned archives for legal precedents or templates (direct "stolen time" that reduces billing potential).
  * **Immediate Proof of Value**: Demonstrating Pillar 4 (Universal File Intelligence) indexing 15,000 PDF court files and finding a legal clause in under 50ms provides an undeniable, instant close in sales meetings.

---

### DECISION 4: SQLite FTS5 for Drive Indexing (The Turbo Engine)
* **Status**: **APPROVED**
* **Context**: Selecting the technology to index local hard drives.
* **Decision**: Implement a local SQLite 3 database using the **FTS5 (Full-Text Search)** extension.
* **Rationale**:
  * **Zero Latency**: Resolves path prefix and substring lookups in `<10ms`, bypassing slow dynamic disk walking.
  * **Zero Dependencies**: Lightweight, natively supported in standard Python/C platforms, and requires no external memory-hog database service running in the background.
