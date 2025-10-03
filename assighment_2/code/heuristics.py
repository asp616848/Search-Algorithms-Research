import random
import time
import numpy as np
from utils import compute_cost


def nearest_neighbor(n, dist_matrix, start=0):
    # optimized NN using numpy for distance comparisons
    unvisited = np.ones(n, dtype=bool)
    tour = [int(start)]
    unvisited[start] = False
    last = start
    while unvisited.any():
        # mask distances to unvisited nodes
        dists = dist_matrix[last]
        # set visited distances to inf so argmin ignores them
        masked = np.where(unvisited, dists, np.inf)
        next_city = int(np.argmin(masked))
        tour.append(next_city)
        unvisited[next_city] = False
        last = next_city
    return tour


def two_opt(tour, dist_matrix, time_limit=None, start_time=None):
    """
    First-improvement 2-opt with O(1) delta evaluation.
    Parameters:
      tour: list or array of node indices
      dist_matrix: numpy 2D array
      time_limit: seconds (float) to stop the search (optional)
      start_time: timestamp to use with time_limit (optional)
    Returns improved tour (list)
    """
    n = len(tour)
    tour = list(tour)
    if n < 4:
        return tour

    if time_limit is not None and start_time is None:
        start_time = time.time()

    improved = True
    # precompute to local vars for speed
    dm = dist_matrix
    while improved:
        improved = False
        # iterate i from 0..n-3, j from i+2..n-1 (avoid adjacent and wrap)
        for i in range(0, n - 2):
            a = tour[i]
            b = tour[(i + 1) % n]
            for j in range(i + 2, n):
                # don't allow swapping the first and last edge in a way that keeps tour invalid
                if i == 0 and j == n - 1:
                    continue
                c = tour[j]
                d = tour[(j + 1) % n]

                # delta = (a-c) + (b-d) - (a-b) - (c-d)
                delta = dm[a, c] + dm[b, d] - dm[a, b] - dm[c, d]
                if delta < -1e-12:
                    # perform 2-opt: reverse segment (i+1..j)
                    tour[i+1:j+1] = reversed(tour[i+1:j+1])
                    improved = True
                    # first-improvement: break to restart outer loops
                    break
                # time check
                if time_limit is not None and (time.time() - start_time) > time_limit:
                    return tour
            if improved:
                # restart search from beginning after improvement
                break
            if time_limit is not None and (time.time() - start_time) > time_limit:
                return tour
    return tour
