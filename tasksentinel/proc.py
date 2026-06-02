import time
import psutil


class ProcessInfo:
    __slots__ = (
        'pid', 'name', 'username', 'cpu_percent', 'memory_percent',
        'memory_rss', 'status', 'num_threads', 'create_time', 'cmdline'
    )

    def __init__(self, pid, name, username, cpu_percent, memory_percent,
                 memory_rss, status, num_threads, create_time, cmdline):
        self.pid = pid
        self.name = name
        self.username = username
        self.cpu_percent = cpu_percent
        self.memory_percent = memory_percent
        self.memory_rss = memory_rss
        self.status = status
        self.num_threads = num_threads
        self.create_time = create_time
        self.cmdline = cmdline or []

    def to_dict(self):
        return {
            'pid': self.pid,
            'name': self.name,
            'username': self.username,
            'cpu_percent': round(self.cpu_percent, 1),
            'memory_percent': round(self.memory_percent, 1),
            'memory_rss': self.memory_rss,
            'status': self.status,
            'num_threads': self.num_threads,
            'create_time': self.create_time,
            'cmdline': ' '.join(self.cmdline) if self.cmdline else '',
        }

    @staticmethod
    def from_dict(data):
        return ProcessInfo(
            pid=data['pid'],
            name=data['name'],
            username=data['username'],
            cpu_percent=data['cpu_percent'],
            memory_percent=data['memory_percent'],
            memory_rss=data['memory_rss'],
            status=data['status'],
            num_threads=data['num_threads'],
            create_time=data['create_time'],
            cmdline=data.get('cmdline', '').split() if data.get('cmdline') else [],
        )


def collect_processes(sort_by='cpu', limit=None):
    procs = []
    seen = set()
    for proc in psutil.process_iter():
        pid = proc.pid
        if pid in seen:
            continue
        seen.add(pid)
        try:
            pinfo = ProcessInfo(
                pid=pid,
                name=proc.name() or '?',
                username=proc.username() or '?',
                cpu_percent=proc.cpu_percent() or 0.0,
                memory_percent=proc.memory_percent() or 0.0,
                memory_rss=proc.memory_info().rss if proc.memory_info() else 0,
                status=proc.status() or '?',
                num_threads=proc.num_threads() or 0,
                create_time=proc.create_time() or 0.0,
                cmdline=proc.cmdline() or [],
            )
            procs.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
            pass

    _sort_processes(procs, sort_by)

    if limit:
        procs = procs[:limit]

    return procs


def _sort_processes(procs, sort_by):
    if sort_by == 'cpu':
        procs.sort(key=lambda p: p.cpu_percent, reverse=True)
    elif sort_by == 'mem':
        procs.sort(key=lambda p: p.memory_percent, reverse=True)
    elif sort_by == 'pid':
        procs.sort(key=lambda p: p.pid)
    elif sort_by == 'name':
        procs.sort(key=lambda p: p.name.lower())


def system_info():
    return {
        'total_memory': psutil.virtual_memory().total,
        'available_memory': psutil.virtual_memory().available,
        'cpu_count': psutil.cpu_count(),
        'cpu_percent_global': psutil.cpu_percent(interval=None),
        'boot_time': psutil.boot_time(),
    }
