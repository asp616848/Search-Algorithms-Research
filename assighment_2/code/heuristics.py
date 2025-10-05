import random
import time
import numpy as np
from utils import compute_cost


def lin_kernighan(
    dist_matrix: 'np.ndarray',
    time_limit: float | None = None,
    seed: int | None = None,
    neighbor_size: int = 20,
    max_no_improve: int = 50,
) -> list[int]:
    """Run a simplified Lin-Kernighan heuristic on the given distance matrix.

    The implementation follows the spirit of Lin-Kernighan by performing
    variable-depth improvements using a sequence of 2-opt moves guided by
    candidate neighbor sets, with occasional double-bridge "kicks" to escape
    local minima. The routine always returns the best tour discovered within
    the allotted time limit.
    """

    n = dist_matrix.shape[0]
    if n <= 1:
        return list(range(n))

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))

    neighbor_size = max(1, min(neighbor_size, n - 1))
    neighbor_lists = np.argsort(dist_matrix, axis=1)[:, 1 : neighbor_size + 1]

    start_time = time.time()
    start_node = random.randrange(n)
    current_tour = _nearest_neighbor(dist_matrix, start_node)
    positions = _build_positions(current_tour)
    best_tour = current_tour[:]
    best_cost = compute_cost(best_tour, dist_matrix)

    no_improve = 0
    kicks_used = 0
    max_kicks = max(1, n // 10)

    while True:
        if time_limit is not None and (time.time() - start_time) >= time_limit:
            break

        current_tour, positions, delta = _best_2opt_move(
            current_tour, positions, dist_matrix, neighbor_lists
        )

        if delta < -1e-9:
            no_improve = 0
            kicks_used = 0
            cost = compute_cost(current_tour, dist_matrix)
            if cost + 1e-9 < best_cost:
                best_cost = cost
                best_tour = current_tour[:]
        else:
            no_improve += 1
            if no_improve >= max_no_improve:
                if time_limit is not None and (time.time() - start_time) >= time_limit:
                    break
                if kicks_used >= max_kicks:
                    break
                current_tour = _double_bridge_move(current_tour)
                positions = _build_positions(current_tour)
                no_improve = 0
                kicks_used += 1
            else:
                continue

    return best_tour


def _nearest_neighbor(dist_matrix: 'np.ndarray', start: int) -> list[int]:
    n = dist_matrix.shape[0]
    unvisited = np.ones(n, dtype=bool)
    tour = [int(start)]
    unvisited[start] = False
    last = start
    while unvisited.any():
        dists = dist_matrix[last]
        masked = np.where(unvisited, dists, np.inf)
        next_city = int(np.argmin(masked))
        tour.append(next_city)
        unvisited[next_city] = False
        last = next_city
    return tour


def _build_positions(tour: list[int]) -> 'np.ndarray':
    positions = np.empty(len(tour), dtype=int)
    for idx, node in enumerate(tour):
        positions[node] = idx
    return positions


def _indices_between(i: int, j: int, n: int) -> list[int]:
    idxs: list[int] = []
    cur = (i + 1) % n
    while True:
        idxs.append(cur)
        if cur == j:
            break
        cur = (cur + 1) % n
    return idxs


def _apply_2opt(tour: list[int], i: int, j: int) -> list[int]:
    n = len(tour)
    if i == j:
        return tour[:]

    indices = _indices_between(i, j, n)
    if len(indices) <= 1:
        return tour[:]

    new_tour = tour[:]
    segment = [tour[idx] for idx in indices][::-1]
    for idx, node in zip(indices, segment):
        new_tour[idx] = node
    return new_tour


def _best_2opt_move(
    tour: list[int],
    positions: 'np.ndarray',
    dist_matrix: 'np.ndarray',
    neighbor_lists: 'np.ndarray',
) -> tuple[list[int], 'np.ndarray', float]:
    n = len(tour)
    best_delta = 0.0
    best_pair: tuple[int, int] | None = None

    dm = dist_matrix
    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        for neighbor in neighbor_lists[a]:
            j = int(positions[int(neighbor)])
            if j == i or j == (i + 1) % n:
                continue

            c = tour[j]
            d = tour[(j + 1) % n]
            if c == a or d == b:
                continue

            delta = dm[a, c] + dm[b, d] - dm[a, b] - dm[c, d]
            if delta < best_delta - 1e-12:
                best_delta = delta
                best_pair = (i, j)

    if best_pair is None:
        return tour, positions, 0.0

    i, j = best_pair
    new_tour = _apply_2opt(tour, i, j)
    new_positions = _build_positions(new_tour)
    return new_tour, new_positions, best_delta


def _double_bridge_move(tour: list[int]) -> list[int]:
    n = len(tour)
    if n < 8:
        shuffled = tour[:]
        random.shuffle(shuffled)
        return shuffled

    while True:
        a, b, c, d = sorted(random.sample(range(n), 4))
        if a == 0 and d == n - 1:
            continue
        if b - a < 2 or c - b < 2 or d - c < 2:
            continue
        break

    part1 = tour[:a]
    part2 = tour[a:b]
    part3 = tour[b:c]
    part4 = tour[c:d]
    part5 = tour[d:]

    new_tour = part1 + part4 + part2 + part3 + part5
    if len(new_tour) != n:
        return tour[:]
    return new_tour
