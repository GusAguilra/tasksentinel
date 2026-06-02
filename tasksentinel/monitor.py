import curses
import time
from datetime import datetime

from .proc import collect_processes


def run_monitor(stdscr, interval=2):
    curses.curs_set(0)
    curses.use_default_colors()
    stdscr.nodelay(1)
    stdscr.timeout(interval * 1000)

    sort_by = 'cpu'
    selected_row = 0
    search_query = ''
    show_help = False

    processes = []
    previous = {}

    while True:
        key = stdscr.getch()

        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('h') or key == ord('H'):
            show_help = not show_help
        elif key == ord('s'):
            sort_by = 'cpu'
        elif key == ord('m'):
            sort_by = 'mem'
        elif key == ord('p'):
            sort_by = 'pid'
        elif key == ord('n'):
            sort_by = 'name'
        elif key in (curses.KEY_UP, ord('k')):
            selected_row = max(0, selected_row - 1)
        elif key in (curses.KEY_DOWN, ord('j')):
            selected_row = min(len(processes) - 1, selected_row + 1)
        elif key == curses.KEY_BACKSPACE or key == 127:
            search_query = search_query[:-1]
        elif key == ord('/'):
            curses.echo()
            curses.curs_set(1)
            stdscr.addstr(curses.LINES - 1, 0, '/')
            search_query = stdscr.getstr(curses.LINES - 1, 1, 60).decode('utf-8', errors='replace')
            curses.noecho()
            curses.curs_set(0)

        processes = collect_processes(sort_by=sort_by)

        if search_query:
            q = search_query.lower()
            processes = [p for p in processes if q in p.name.lower() or q in str(p.pid)]

        if show_help:
            _draw_help(stdscr)
        else:
            _draw_dashboard(stdscr, processes, selected_row, sort_by, search_query, interval, previous)

        previous = {p.pid: p for p in processes}


def _format_rss(rss):
    if rss >= 1073741824:
        return f'{rss / 1073741824:.1f}G'
    elif rss >= 1048576:
        return f'{rss / 1048576:.1f}M'
    elif rss >= 1024:
        return f'{rss / 1024:.1f}K'
    return f'{rss}B'


def _draw_dashboard(stdscr, processes, selected_row, sort_by, search_query, interval, previous):
    rows, cols = stdscr.getmaxyx()
    title = f' TaskSentinel v0.1.0 '
    header = f' [Q]uit  [S]ort:CPU  S[o]rt:MEM  [/]earch  [H]elp  '
    stdscr.attron(curses.A_REVERSE)
    stdscr.addstr(0, 0, title)
    stdscr.addstr(0, len(title), header.ljust(cols - len(title) - 30))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stdscr.addstr(0, cols - len(now) - 3, now)
    stdscr.attroff(curses.A_REVERSE)

    if search_query:
        stdscr.addstr(1, 0, f' Search: {search_query}', curses.A_BOLD)
    stdscr.addstr(1 if not search_query else 2, 0, '-' * cols)

    table_header = f'{"PID":>7} {"USER":<8} {"CPU%":>6} {"MEM%":>6} {"RSS":>7} {"THR":>4} {"STATUS":<6} NAME'
    status_line = 1 if not search_query else 2
    stdscr.attron(curses.A_BOLD)
    stdscr.addstr(status_line + 1, 0, table_header[:cols - 1])
    stdscr.attroff(curses.A_BOLD)
    stdscr.addstr(status_line + 2, 0, '-' * cols)

    line = status_line + 3
    max_lines = rows - line - 2

    if selected_row >= len(processes):
        selected_row = max(0, len(processes) - 1)

    start_idx = max(0, selected_row - max_lines // 2)
    visible = processes[start_idx:start_idx + max_lines]

    for i, p in enumerate(visible):
        real_idx = start_idx + i
        if real_idx == selected_row:
            stdscr.attron(curses.A_REVERSE)

        cpu = p.cpu_percent
        mem = p.memory_percent
        color_pair = 0
        if cpu > 80:
            color_pair = 1
        elif cpu > 50:
            color_pair = 2

        rss = _format_rss(p.memory_rss)
        row_text = f'{p.pid:>7} {p.username[:8]:<8} {cpu:>5.1f}% {mem:>5.1f}% {rss:>7} {p.num_threads:>4} {p.status[:6]:<6} {p.name[:cols-50]}'

        stdscr.addstr(line, 0, row_text[:cols - 1], color_pair)
        if real_idx == selected_row:
            stdscr.attroff(curses.A_REVERSE)
        line += 1

    if not processes:
        stdscr.addstr(line, 0, ' No processes found', curses.A_DIM)

    # Bottom bar
    stdscr.attron(curses.A_REVERSE)
    elapsed = time.strftime('%H:%M:%S', time.gmtime(time.time()))
    sort_indicator = {'cpu': 'CPU', 'mem': 'MEM', 'pid': 'PID', 'name': 'NAME'}.get(sort_by, 'CPU')
    bottom = f' Sort: {sort_indicator}  |  Processes: {len(processes)}  |  Refresh: {interval}s  |  {elapsed}'
    stdscr.addstr(rows - 1, 0, bottom.ljust(cols - 1))
    stdscr.attroff(curses.A_REVERSE)

    stdscr.refresh()


def _draw_help(stdscr):
    rows, cols = stdscr.getmaxyx()
    stdscr.clear()
    help_lines = [
        'TaskSentinel Help',
        '=' * (cols - 1),
        '',
        '  q / Q         Quit',
        '  s             Sort by CPU',
        '  m             Sort by Memory',
        '  p             Sort by PID',
        '  n             Sort by Name',
        '  /             Search by name or PID',
        '  ↑/k ↓/j      Navigate process list',
        '  h / H         Toggle this help',
        '',
        'Press h to return to the dashboard.',
    ]
    for i, line in enumerate(help_lines):
        stdscr.addstr(i, 0, line[:cols - 1])
    stdscr.refresh()


def run_monitor_wrapper(interval=2):
    curses.wrapper(lambda stdscr: run_monitor(stdscr, interval))
