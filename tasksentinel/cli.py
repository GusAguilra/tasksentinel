import argparse
import json
import subprocess
import sys
import time
from datetime import datetime

from .proc import collect_processes, system_info
from .snapshot import save as snap_save, load as snap_load, list_snapshots as snap_list
from .diff import diff_snapshots
from .monitor import run_monitor_wrapper


def cmd_list(args):
    processes = collect_processes(sort_by=args.sort, limit=args.limit)

    if args.json:
        data = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'system': system_info(),
            'count': len(processes),
            'processes': [p.to_dict() for p in processes],
        }
        print(json.dumps(data, indent=2))
        return

    header = f'{"PID":>7} {"USER":<8} {"CPU%":>6} {"MEM%":>6} {"RSS":>8} {"THR":>4} {"STATUS":<6} {"NAME":<20} {"CMD"}'
    print(f'TaskSentinel — {len(processes)} processes (sorted by {args.sort})')
    print('-' * len(header))
    print(header)
    print('-' * len(header))
    for p in processes:
        rss = _fmt_rss(p.memory_rss)
        cmd = ' '.join(p.cmdline) if p.cmdline else p.name
        print(f'{p.pid:>7} {p.username[:8]:<8} {p.cpu_percent:>5.1f}% {p.memory_percent:>5.1f}% {rss:>8} {p.num_threads:>4} {p.status[:6]:<6} {p.name[:20]:<20} {cmd[:60]}')


def cmd_exec(args):
    command = args.command
    if not command:
        print('error: no command specified')
        sys.exit(1)

    print(f'[tasksentinel] Taking snapshot before: {command}')
    before_path, before_count = snap_save(name=f'before_{int(time.time())}')

    print(f'[tasksentinel] Running: {" ".join(command)}')
    print('─' * 60)
    start = time.time()
    result = subprocess.run(command)
    elapsed = time.time() - start
    print('─' * 60)
    print(f'[tasksentinel] Finished in {elapsed:.2f}s (exit code: {result.returncode})')

    print(f'[tasksentinel] Taking snapshot after...')
    after_path, after_count = snap_save(name=f'after_{int(time.time())}')

    before = snap_load(before_path)
    after = snap_load(after_path)

    if before and after:
        diff = diff_snapshots(before, after)
        _print_diff(diff)


def cmd_snap(args):
    if args.action == 'save':
        path, count = snap_save(name=args.name)
        print(f'Snapshot saved: {path} ({count} processes)')

    elif args.action == 'list':
        snapshots = snap_list()
        if not snapshots:
            print('No snapshots found.')
            return
        print(f'{"#":>3}  {"NAME":<25}  {"DATE":<22}  {"PROCESSES":>9}')
        print('─' * 65)
        for s in snapshots:
            print(f'{s["id"]:>3}  {s["name"]:<25}  {s["datetime"]:<22}  {s["processes"]:>9}')

    elif args.action == 'diff':
        if len(args.ids) < 2:
            print('error: need two snapshot IDs to diff')
            sys.exit(1)
        before = snap_load(args.ids[0])
        after = snap_load(args.ids[1])
        if not before or not after:
            print('error: snapshot not found')
            sys.exit(1)
        diff = diff_snapshots(before, after)

        if args.json:
            print(json.dumps(diff, indent=2, default=str))
        else:
            _print_diff(diff)


def cmd_watch(args):
    run_monitor_wrapper(interval=args.interval)


def _print_diff(diff):
    new = diff['new']
    terminated = diff['terminated']
    changed = diff['changed']

    print()
    if new:
        print(f'  ▶ New processes ({len(new)})')
        print(f'  {"PID":>7} {"NAME":<20} {"CPU%":>6} {"MEM%":>6} {"RSS":>8}')
        for p in new:
            rss = _fmt_rss(p.get('memory_rss', 0))
            print(f'  {p["pid"]:>7} {p["name"][:20]:<20} {p.get("cpu_percent", 0):>5.1f}% {p.get("memory_percent", 0):>5.1f}% {rss:>8}')
        print()

    if terminated:
        print(f'  ◇ Terminated processes ({len(terminated)})')
        print(f'  {"PID":>7} {"NAME":<20} {"CPU% (was)":>10}')
        for p in terminated:
            print(f'  {p["pid"]:>7} {p["name"][:20]:<20} {p.get("cpu_percent", 0):>9.1f}%')
        print()

    if changed:
        print(f'  ◆ Changed processes ({len(changed)})')
        print(f'  {"PID":>7} {"NAME":<20} {"CPU Δ":>7} {"MEM Δ":>7}')
        for p in changed:
            cpu_sign = '+' if p['cpu_diff'] > 0 else ''
            mem_sign = '+' if p['mem_diff'] > 0 else ''
            cpu_str = f'{cpu_sign}{p["cpu_diff"]:.1f}%'
            mem_str = f'{mem_sign}{p["mem_diff"]:.1f}%'
            print(f'  {p["pid"]:>7} {p["name"][:20]:<20} {cpu_str:>7} {mem_str:>7}')
        print()

    if not new and not terminated and not changed:
        print('  No significant differences found.')
        print()


def _fmt_rss(rss):
    if rss >= 1073741824:
        return f'{rss / 1073741824:.1f}G'
    elif rss >= 1048576:
        return f'{rss / 1048576:.1f}M'
    elif rss >= 1024:
        return f'{rss / 1024:.1f}K'
    return f'{rss}B'


def main():
    parser = argparse.ArgumentParser(
        prog='tasksentinel',
        description='A lightweight CLI tool for monitoring Linux processes.',
    )
    subparsers = parser.add_subparsers(dest='command')

    # list
    list_parser = subparsers.add_parser('list', help='List processes')
    list_parser.add_argument('--sort', choices=['cpu', 'mem', 'pid', 'name'], default='cpu')
    list_parser.add_argument('--limit', type=int, default=None)
    list_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # exec
    exec_parser = subparsers.add_parser('exec', help='Run a command with before/after snapshots')
    exec_parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run')

    # snap
    snap_parser = subparsers.add_parser('snap', help='Manage snapshots')
    snap_sub = snap_parser.add_subparsers(dest='action')
    snap_save_p = snap_sub.add_parser('save', help='Save a snapshot')
    snap_save_p.add_argument('--name', default=None, help='Snapshot name')
    snap_list_p = snap_sub.add_parser('list', help='List snapshots')
    snap_diff_p = snap_sub.add_parser('diff', help='Diff two snapshots')
    snap_diff_p.add_argument('ids', nargs=2, help='Snapshot IDs or names')
    snap_diff_p.add_argument('--json', action='store_true', help='Output as JSON')

    # watch
    watch_parser = subparsers.add_parser('watch', help='Live process monitor (curses)')
    watch_parser.add_argument('--interval', '-i', type=int, default=2, help='Refresh interval in seconds')

    args = parser.parse_args()

    if args.command == 'list':
        cmd_list(args)
    elif args.command == 'exec':
        cmd_exec(args)
    elif args.command == 'snap':
        cmd_snap(args)
    elif args.command == 'watch':
        cmd_watch(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
