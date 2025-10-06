import sys
import signal
import time

import numpy as np

from utils import read_input, write_tour, compute_cost
from heuristics import run_ga_lin_kernighan


# Global flag for graceful shutdown
interrupted = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global interrupted
    interrupted = True
    print("\n\nInterrupt received. Cleaning up and saving best solution...", file=sys.stderr)
    # Don't exit immediately - let the finally block handle cleanup

def main():
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    overall_start = time.time()
    # max runtime in seconds (user target: 300s for 200 nodes)
    MAX_RUNTIME = 10.0

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
        seed = int(np.random.default_rng().integers(0, 2**32, dtype=np.uint32))
        # seed = 1934124118
        print(f"Using random seed: {seed}")
        best_from_ga, progress = run_ga_lin_kernighan(
            dist_matrix, time_limit=available, seed=seed, output_file=output_file
        )

        # Read what's been written to the output file to set bookkeeping
        try:
            with open(output_file, 'r') as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
            tours_logged = len(lines)
            if tours_logged:
                last_written = list(map(int, lines[-1].split()))
                best_cost = compute_cost(last_written, dist_matrix)
                best_tour = last_written[:]
        except Exception:
            # if reading fails, fall back to progress returned
            for tour in progress:
                c = compute_cost(tour, dist_matrix)
                if c < best_cost:
                    best_cost = c
                    best_tour = list(tour)
    except KeyboardInterrupt:
        # Catch the interrupt here so we can still save results
        print("\nKeyboardInterrupt caught in main", file=sys.stderr)

    finally:
        if best_tour is None:
            try:
                with open(output_file, 'r') as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
                tours_logged = len(lines)
                if tours_logged:
                    last_written = list(map(int, lines[-1].split()))
                    best_tour = last_written[:]
                    best_cost = compute_cost(best_tour, dist_matrix)
            except Exception:
                pass

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
