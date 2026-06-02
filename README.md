# TaskSentinel

A lightweight CLI tool for monitoring Linux processes. Works entirely locally with no external data sharing — only reads from `/proc` via `psutil`.

## Features

- **`list`** — List processes sorted by CPU, memory, PID, or name
- **`watch`** — Real-time terminal dashboard (curses-based)
- **`exec`** — Run a command and automatically snapshot before/after, then show what changed
- **`snap save`** — Save a snapshot of all running processes
- **`snap list`** — List saved snapshots
- **`snap diff`** — Compare two snapshots to find new, terminated, or changed processes

## Installation

```bash
pip install tasksentinel
```

Or from source:

```bash
git clone https://github.com/yourusername/tasksentinel.git
cd tasksentinel
pip install -e .
```

## Usage

```bash
# List top 10 processes by CPU
tasksentinel list --sort cpu --limit 10

# Output as JSON (for scripting/pipe)
tasksentinel list --sort mem --limit 5 --json

# Run a command and snapshot before/after
tasksentinel exec -- npm run build

# Real-time monitoring dashboard
tasksentinel watch
tasksentinel watch --interval 1

# Snapshots
tasksentinel snap save --name before-update
tasksentinel snap list
tasksentinel snap diff 1 2
```

## Requirements

- Python 3.10+
- `psutil` (reads local `/proc` — no network access)

## License

MIT
