import sys
import random
from utils import read_input, write_tour, compute_cost
from heuristics import lin_kernighan
import time


def main():
    overall_start = time.time()
    # max runtime in seconds (user target: 300s for 200 nodes)
    MAX_RUNTIME = 300.0

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
        while True:
            now = time.time()
            elapsed = now - overall_start
            remaining = MAX_RUNTIME - elapsed
            if remaining <= buffer:
                break

            attempts += 1
            # give the first LK run the majority of the remaining budget, later runs get capped
            per_attempt = remaining - buffer
            if attempts > 1:
                per_attempt = min(per_attempt, 60.0)

            if per_attempt <= 0:
                break

            seed = random.randint(0, 2**32 - 1)
            tour = lin_kernighan(dist_matrix, time_limit=per_attempt, seed=seed)
            write_tour(output_file, tour)

            c = compute_cost(tour, dist_matrix)
            if c < best_cost:
                best_cost = c
                best_tour = list(tour)

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
