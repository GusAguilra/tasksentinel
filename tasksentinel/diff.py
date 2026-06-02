from . proc import ProcessInfo


def diff_snapshots(before, after):
    before_procs = {p['pid']: p for p in before.get('processes', [])}
    after_procs = {p['pid']: p for p in after.get('processes', [])}

    before_pids = set(before_procs.keys())
    after_pids = set(after_procs.keys())

    new_pids = after_pids - before_pids
    gone_pids = before_pids - after_pids
    common_pids = before_pids & after_pids

    new = [after_procs[pid] for pid in sorted(new_pids)]
    terminated = [before_procs[pid] for pid in sorted(gone_pids)]

    changed = []
    for pid in sorted(common_pids):
        b = before_procs[pid]
        a = after_procs[pid]
        cpu_diff = abs((a['cpu_percent'] or 0) - (b['cpu_percent'] or 0))
        mem_diff = abs((a['memory_percent'] or 0) - (b['memory_percent'] or 0))
        if cpu_diff > 1.0 or mem_diff > 1.0:
            changed.append({
                'pid': pid,
                'name': a['name'],
                'cpu_before': b['cpu_percent'],
                'cpu_after': a['cpu_percent'],
                'cpu_diff': round((a['cpu_percent'] or 0) - (b['cpu_percent'] or 0), 1),
                'mem_before': b['memory_percent'],
                'mem_after': a['memory_percent'],
                'mem_diff': round((a['memory_percent'] or 0) - (b['memory_percent'] or 0), 1),
            })

    return {
        'new': new,
        'terminated': terminated,
        'changed': changed,
        'system_before': before.get('system', {}),
        'system_after': after.get('system', {}),
        'time_before': before.get('timestamp', 0),
        'time_after': after.get('timestamp', 0),
    }
