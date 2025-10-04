import sys
import random
import time

from utils import read_input, write_tour, compute_cost
from heuristics import run_ga_lin_kernighan

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

    # Track best solution data for the summary
    best_tour = None
    best_cost = float('inf')
    tours_logged = 0
    last_written = None
    buffer = 0.5

    try:
        available = max(0.0, MAX_RUNTIME - buffer)
        seed = random.randrange(2**32)
        best_from_ga, progress = run_ga_lin_kernighan(
            dist_matrix, time_limit=available, seed=seed
        )

        for tour in progress:
            write_tour(output_file, tour)
            tours_logged += 1
            last_written = tour

            c = compute_cost(tour, dist_matrix)
            if c < best_cost:
                best_cost = c
                best_tour = list(tour)

        # ensure GA best is captured even if not in progress
        if best_tour is None and best_from_ga is not None:
            best_cost = compute_cost(best_from_ga, dist_matrix)
            best_tour = list(best_from_ga)
            write_tour(output_file, best_tour)
            tours_logged += 1
            last_written = best_tour

    finally:
        # print summary including best cost so user sees it even after Ctrl+C
        end_time = time.time()
        execution_time = end_time - overall_start
        print(f"Total execution time: {execution_time:.4f} seconds")
        print(f"Tours logged: {tours_logged}")
        if best_tour is not None:
            print(f"Best tour cost: {best_cost:.6f}")
            # Ensure the output file's last row is the best tour. Append it so it's the final line.
            try:
                if last_written is None or best_tour != last_written:
                    write_tour(output_file, best_tour)
            except Exception:
                # If writing fails for some reason, still exit gracefully.
                pass
        else:
            print("No tour was produced.")


if __name__ == "__main__":
    main()
