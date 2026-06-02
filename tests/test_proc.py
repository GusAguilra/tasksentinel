from tasksentinel.proc import collect_processes, ProcessInfo, system_info


def test_collect_processes_returns_list():
    procs = collect_processes()
    assert isinstance(procs, list)
    assert len(procs) > 0


def test_collect_processes_sorts_by_cpu():
    procs = collect_processes(sort_by='cpu')
    for i in range(len(procs) - 1):
        assert procs[i].cpu_percent >= procs[i + 1].cpu_percent


def test_collect_processes_sorts_by_mem():
    procs = collect_processes(sort_by='mem')
    for i in range(len(procs) - 1):
        assert procs[i].memory_percent >= procs[i + 1].memory_percent


def test_collect_processes_limit():
    procs = collect_processes(limit=5)
    assert len(procs) <= 5


def test_process_info_fields():
    procs = collect_processes(limit=1)
    assert len(procs) == 1
    p = procs[0]
    assert isinstance(p.pid, int)
    assert isinstance(p.name, str)
    assert isinstance(p.cpu_percent, (int, float))


def test_process_info_to_from_dict():
    procs = collect_processes(limit=1)
    if procs:
        p = procs[0]
        d = p.to_dict()
        restored = ProcessInfo.from_dict(d)
        assert restored.pid == p.pid
        assert restored.name == p.name


def test_system_info():
    info = system_info()
    assert 'total_memory' in info
    assert 'cpu_count' in info
    assert info['cpu_count'] > 0
