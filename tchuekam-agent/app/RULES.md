# TCHUEKAM Code Assistant in Google One AI Pro

## NON-NEGOTIABLE AI ASSISTANT RULES: SOVEREIGN ENGINE

To maintain the architectural integrity of the **Sovereign Engine**, any AI assistant (including subsequent sessions of myself) working on this codebase **MUST strictly adhere to these rules at all times**. 

Failure to follow these protocols results in code degradation and ghost debugging.

---

### RULE 1: ANTI-GHOST DEBUGGING PROTOCOL
* **No Blind Refactoring**: If the user reports "this is not working," the AI must NOT immediately alter, delete, or rewrite existing code. 
* **Diagnosis First**: Run diagnostic commands (e.g. check environment variables, verify directory structures, test file existences) to isolate the exact cause of failure before editing a single line.
* **Respect Existing Work**: If a capability was verified as functional in `PROGRESS.md`, assume the code is correct. Look for path configuration mismatches, locked system files, or permission blocks instead of rewriting the code structure.

---

### RULE 2: ARCHITECTURAL INTEGRITY (DECISIONS & BLUEPRINT)
* **Never Contradict recorded Decisions**: Consult `DECISIONS.md` before proposing any architectural change. 
* **The Single-Engine Absolute**: Never write separate codebases for separate business sectors. All adaptability must reside in the *dynamic data context* layer. Custom features must be written as external plugins, keeping the core engine 100% unified.
* **100% Offline Integrity**: Never introduce library dependencies that require online token calls or send data to external APIs. All indexing, vector embedding generation, and document processing must resolve locally on the host machine.

---

### RULE 3: ZERO PLACEHOLDERS
* **Production-Grade Writes**: Every code edit, tool injection, or script must be written in full.
* **No Code Truncations**: Never use `// TODO` or `# ... (rest of code remains the same)` inside a code block you are creating or modifying. 

---

### RULE 4: CORE EXECUTOR SAFETY
* **Isolate Extensions**: When adding capabilities, write them as modular modules in `tools/` or `skills/`.
* **Protect the Core Loop**: Do not refactor or modify core execution files (`run_agent.py`, `cli.py`, `tchuekam_state.py`) unless a capability specifically requires modifying the base agent loop.

---

### RULE 5: WINDOWS FILE PHYSICAL PATH SAFETIES
* **MAX_PATH Handling**: Because Windows native paths are restricted to 260 characters by default, always account for long path limits:
  * When executing file operations on deep directories, prefix absolute paths with `\\?\` where supported.
  * For deep folder deletions, use the **Robocopy Mirroring Technique** instead of standard `shutil.rmtree()` to bypass path limit crashes.

---

### RULE 6: TERMINAL-PASS VALIDATION MANDATE
* **Execution over Cleanliness**: Code cleanliness alone is irrelevant. Code is valid and accepted IF AND ONLY IF it successfully executes and passes functional verification within the local terminal.
* **Continuous Loop Probing**: When implementing or fixing features, follow this sequence: Propose Command -> Analyze Terminal Output -> Debug -> Patch -> Test. Loop this sequence repeatedly until terminal execution reports 0 functional errors.
