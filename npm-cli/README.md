# @tchuekam/cli

**Tchuekam Sovereign Enterprise Intelligence Platform — Global CLI Launcher**

> Deploy a full local AI workstation with a single command.

---

## Requirements

| Prerequisite | Minimum Version |
|---|---|
| Node.js | 20.x |
| Python | 3.10+ |

---

## Installation

### Global (production — recommended)

```bash
npm install -g @tchuekam/cli
```

### Local dev (inside repo)

```bash
cd npm-cli
npm link
```

---

## Usage

### Start the workstation daemon

```bash
tchuekam start
```

This will:
1. Verify Python 3.10+ is installed and accessible via `PATH`
2. Resolve and launch the backend daemon (`tchuekam_cli.main`)
3. Open the browser UI at `http://127.0.0.1:9119`

### Options

| Flag | Description | Default |
|---|---|---|
| `-p, --port <number>` | Port for the local loopback server | `9119` |
| `-V, --version` | Print the CLI version | — |
| `-h, --help` | Show command help | — |

### Example

```bash
# Start on a custom port
tchuekam start --port 8080
```

---

## Architecture

```
@tchuekam/cli (npm)
      │
      ▼
  launcher.js  ──► python -m tchuekam_cli.main web --port 9119
                         │
                         ▼
                  TchuEkaM Backend (FastAPI / Agentic Core)
```

The CLI wrapper is a thin Node.js shim. The intelligence lives entirely in the Python backend.

---

## License

MIT © Tchuekam Research
