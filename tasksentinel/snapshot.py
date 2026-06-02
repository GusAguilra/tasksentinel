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

    # If it's already a full path to an existing file, use it directly
    if os.path.exists(name_or_id):
        return name_or_id

    # If it ends with .json, try as a full path in snapshot dir
    if name_or_id.endswith('.json'):
        path = os.path.join(SNAPSHOT_DIR, name_or_id)
        if os.path.exists(path):
            return path

    # Try as a name (adds .json extension automatically)
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


def delete_snapshots(ids=None, all_flag=False, older_than=0):
    snapshots = list_snapshots()
    deleted = []

    if all_flag:
        for s in snapshots:
            try:
                os.remove(s['path'])
                deleted.append(s['name'])
            except OSError:
                pass
        return deleted

    if older_than > 0:
        cutoff = time.time() - (older_than * 86400)
        ids_set = set(ids or [])
        for s in snapshots:
            ts = datetime.strptime(s['datetime'], '%Y-%m-%d %H:%M:%S').timestamp()
            if ts < cutoff and s['name'] not in ids_set:
                try:
                    os.remove(s['path'])
                    deleted.append(s['name'])
                except OSError:
                    pass
        return deleted

    if ids:
        ids_set = set(ids)
        for snap in snapshots:
            if str(snap['id']) in ids_set or snap['name'] in ids_set:
                try:
                    os.remove(snap['path'])
                    deleted.append(snap['name'])
                except OSError:
                    pass
    return deleted
