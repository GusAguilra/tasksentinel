import sys
import time
import multiprocessing as mp


def eat_cpu():
    while True:
        [x ** 2 for x in range(50000)]


if __name__ == '__main__':
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    print(f"[test_consume] Spawning 3 CPU-hungry processes...")
    procs = [mp.Process(target=eat_cpu) for _ in range(3)]

    for p in procs:
        p.start()
        print(f"[test_consume] Spawned PID {p.pid}")

    print(f"[test_consume] Eating CPU for {duration}s...")
    time.sleep(duration)

    for p in procs:
        p.terminate()
        p.join()

    print("[test_consume] Done")
