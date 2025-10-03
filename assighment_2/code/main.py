import sys
import random
from utils import read_input, write_tour, compute_cost
from heuristics import nearest_neighbor, two_opt
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

    # single NN + 2-opt
    now = time.time()
    time_left = MAX_RUNTIME - (now - overall_start)
    init_tour = nearest_neighbor(n, dist_matrix, start=random.randint(0, n-1))
    write_tour(output_file, init_tour)

    # run 2-opt with time limit guard (leave a small buffer)
    buffer = 0.5
    time_for_local = max(0.0, time_left - buffer)
    improved_tour = two_opt(init_tour, dist_matrix, time_limit=time_for_local, start_time=now)
    write_tour(output_file, improved_tour)

    # controlled random restarts until time runs out
    attempts = 0
    while True:
        attempts += 1
        now = time.time()
        elapsed = now - overall_start
        if elapsed >= MAX_RUNTIME - buffer:
            break
        # allocate a small chunk per restart
        per_restart = min(10.0, MAX_RUNTIME - elapsed - buffer)
        tour = nearest_neighbor(n, dist_matrix, start=random.randint(0, n-1))
        tour = two_opt(tour, dist_matrix, time_limit=per_restart, start_time=now)
        write_tour(output_file, tour)

    end_time = time.time()
    execution_time = end_time - overall_start
    print(f"Total execution time: {execution_time:.4f} seconds")
    print(f"Random restarts performed: {attempts}")


if __name__ == "__main__":
    main()
