# TaskSentinel

A lightweight CLI tool for monitoring Linux processes. Works entirely locally with no external data sharing — only reads from `/proc` via `psutil`.

## Features

- **`list`** — List processes sorted by CPU, memory, PID, or name
- **`watch`** — Real-time terminal dashboard (curses-based) with search and sorting
- **`exec`** — Run any command and automatically capture before/during/after snapshots to see what processes were spawned, terminated, or changed
- **`snap save`** — Save a point-in-time snapshot of all running processes
- **`snap list`** — List all saved snapshots
- **`snap diff`** — Compare two snapshots to find new, terminated, or changed processes
- **`snap delete`** — Delete snapshots by ID, name, all, or older than N days

## Requirements

- Python 3.10+
- `psutil` (reads local `/proc` — no network access)

## Installation

```bash
git clone https://github.com/GusAguilra/tasksentinel.git
cd tasksentinel
pip install -e .
```

## Usage

### List processes
```bash
# Top 10 processes by CPU usage
tasksentinel list --sort cpu --limit 10

# Top 5 by memory, JSON output (for scripting)
tasksentinel list --sort mem --limit 5 --json
```

### Watch live dashboard
```bash
# Real-time process monitor (curses interface)
tasksentinel watch

# Custom refresh interval
tasksentinel watch --interval 1
```
Controls inside watch: `s` sort CPU, `m` sort memory, `p` sort PID, `/` search, `Esc` clear search, `q` quit.

### Execute and track (killer feature)
```bash
# Run any command and see what processes it spawned, killed, or affected
tasksentinel exec -- npm run build
tasksentinel exec -- python3 script.py
tasksentinel exec -- sleep 5
```
Takes snapshots before, during (1s after start), and after execution, then shows a diff.

### Manage snapshots
```bash
# Save a named snapshot
tasksentinel snap save --name before-update

# List all snapshots
tasksentinel snap list

# Compare two snapshots
tasksentinel snap diff 1 2
tasksentinel snap diff before-update after-update

# Delete snapshots
tasksentinel snap delete 1               # by ID
tasksentinel snap delete before-update   # by name
tasksentinel snap delete --all           # all snapshots
tasksentinel snap delete --older-than 7  # older than 7 days
```

## License

MIT
