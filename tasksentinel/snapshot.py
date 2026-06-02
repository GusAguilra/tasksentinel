import os
import json
import time
from datetime import datetime

from .proc import collect_processes, system_info

SNAPSHOT_DIR = os.path.expanduser('~/.tasksentinel/snapshots')


def _ensure_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def save(name=None):
    _ensure_dir()
    if not name:
        name = datetime.now().strftime('%Y%m%d_%H%M%S')

    processes = collect_processes()
    data = {
        'name': name,
        'timestamp': time.time(),
        'datetime': datetime.now().isoformat(),
        'system': system_info(),
        'processes': [p.to_dict() for p in processes],
    }

    path = os.path.join(SNAPSHOT_DIR, f'{name}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

    return path, len(processes)


def load(name_or_id):
    _ensure_dir()
    path = _resolve_path(name_or_id)
    if not path:
        return None
    with open(path) as f:
        data = json.load(f)
    return data


def _resolve_path(name_or_id):
    name_or_id = str(name_or_id)
    # Try as a full name first
    path = os.path.join(SNAPSHOT_DIR, f'{name_or_id}.json')
    if os.path.exists(path):
        return path

    # Try as an index number
    snapshots = list_snapshots()
    for snap in snapshots:
        if str(snap['id']) == name_or_id:
            return snap['path']

    return None


def list_snapshots():
    _ensure_dir()
    snapshots = []
    if not os.path.isdir(SNAPSHOT_DIR):
        return snapshots

    for fname in sorted(os.listdir(SNAPSHOT_DIR)):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(SNAPSHOT_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            count = len(data.get('processes', []))
            ts = data.get('timestamp', 0)
            dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            snapshots.append({
                'id': len(snapshots) + 1,
                'name': data.get('name', fname[:-5]),
                'datetime': dt,
                'processes': count,
                'path': path,
            })
        except (json.JSONDecodeError, OSError):
            continue

    return snapshots
