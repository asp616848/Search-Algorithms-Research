import sys
import time
import os
import numpy as np
from multiprocessing import Pool, cpu_count
from utils import read_input, write_tour, compute_cost
from heuristics import nearest_neighbor, two_opt

# Module-level globals used by worker processes (set in worker_init)
_WORK_DM = None
_WORK_N = None
_WORK_RNG = None


def worker_init(dm, nnodes, seed_offset):
    """Initializer for worker processes. Stores the distance matrix and node count
    in module globals so worker_task can access them without re-passing large args.
    seed_offset is used to seed a per-worker numpy RNG.
    """
    global _WORK_DM, _WORK_N, _WORK_RNG
    _WORK_DM = dm
    _WORK_N = nnodes
    try:
        _WORK_RNG = np.random.default_rng(int(seed_offset) + os.getpid())
    except Exception:
        _WORK_RNG = np.random.default_rng(int(seed_offset))


def worker_task(time_slice, seed):
    """Performs one NN + 2-opt run in a worker process and returns (cost, tour).
    time_slice: float seconds to allow two_opt to run.
    seed: integer seed used to pick a start city.
    """
    # Access globals set by worker_init
    global _WORK_DM, _WORK_N, _WORK_RNG
    if _WORK_DM is None or _WORK_N is None:
        raise RuntimeError("Worker not initialized with distance matrix")
    # derive a start city from seed (deterministic, avoids python's random)
    start = int(int(seed) % int(_WORK_N))
    tour = nearest_neighbor(_WORK_N, _WORK_DM, start=start)
    tour = two_opt(tour, _WORK_DM, time_limit=time_slice, start_time=time.time())
    cost = compute_cost(tour, _WORK_DM)
    return (cost, tour)

def main():
    overall_start = time.time()
    # max runtime in seconds (user target: 300s for 200 nodes)
    MAX_RUNTIME = 60.0

    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python main.py input.txt output.txt [max_seconds]")
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]
    if len(sys.argv) == 4:
        try:
            MAX_RUNTIME = float(sys.argv[3])
        except ValueError:
            pass

    # Read input
    metric, n, dist_matrix = read_input(input_file)

    # Open output file fresh
    open(output_file, 'w').close()

    # We'll track the best tour and its cost so we can report it at the end
    best_tour = None
    best_cost = float('inf')
    attempts = 0
    buffer = 0.5

    try:
        # single NN + 2-opt from a deterministic numpy RNG start
        now = time.time()
        time_left = MAX_RUNTIME - (now - overall_start)
        rng = np.random.default_rng()
        init_start = int(rng.integers(0, n))
        init_tour = nearest_neighbor(n, dist_matrix, start=init_start)
        write_tour(output_file, init_tour)
        # update best
        c = compute_cost(init_tour, dist_matrix)
        if c < best_cost:
            best_cost = c
            best_tour = list(init_tour)

        # run 2-opt with time limit guard (leave a small buffer)
        time_for_local = max(0.0, time_left - buffer)
        improved_tour = two_opt(init_tour, dist_matrix, time_limit=time_for_local, start_time=time.time())
        write_tour(output_file, improved_tour)
        c = compute_cost(improved_tour, dist_matrix)
        if c < best_cost:
            best_cost = c
            best_tour = list(improved_tour)

        # parallel restarts using multiprocessing.Pool
        # We'll create tasks that run NN + two_opt for a small time slice.
        # Use a worker initializer to set globals so we avoid repeatedly sending the dist matrix.

        # how many parallel workers (leave one core free)
        workers = max(1, cpu_count() - 1)
        per_restart = 10.0
        pool = Pool(processes=workers, initializer=worker_init, initargs=(dist_matrix, n, int(rng.integers(1, 1<<30))))
        try:
            # submit tasks until time runs out
            while True:
                attempts += 1
                now = time.time()
                elapsed = now - overall_start
                if elapsed >= MAX_RUNTIME - buffer:
                    break
                time_remaining = MAX_RUNTIME - elapsed - buffer
                if time_remaining <= 0:
                    break
                slice_time = min(per_restart, time_remaining)

                # build seeds for each worker from RNG
                seeds = [int(x) for x in rng.integers(0, 1<<30, size=workers)]
                try:
                    results = pool.starmap(worker_task, [(slice_time, s) for s in seeds])
                except KeyboardInterrupt:
                    # allow Ctrl+C to stop workers quickly
                    pool.terminate()
                    pool.join()
                    raise

                for cost, tour in results:
                    write_tour(output_file, tour)
                    if cost < best_cost:
                        best_cost = cost
                        best_tour = list(tour)
        finally:
            try:
                pool.close()
                pool.join()
            except Exception:
                pass

    finally:
        # print summary including best cost so user sees it even after Ctrl+C
        end_time = time.time()
        execution_time = end_time - overall_start
        print(f"Total execution time: {execution_time:.4f} seconds")
        print(f"Random restarts performed: {attempts}")
        if best_tour is not None:
            print(f"Best tour cost: {best_cost:.6f}")
            # Ensure the output file's last row is the best tour. Append it so it's the final line.
            try:
                write_tour(output_file, best_tour)
            except Exception:
                # If writing fails for some reason, still exit gracefully.
                pass
        else:
            print("No tour was produced.")


if __name__ == "__main__":
    main()
