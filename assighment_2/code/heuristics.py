import random
import time
from typing import List, Sequence, Tuple

import numpy as np

from utils import compute_cost


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_ga_lin_kernighan(
    dist_matrix: np.ndarray,
    time_limit: float | None = None,
    seed: int | None = None,
    population_size: int = 60,
    elite_fraction: float = 0.15,
    mutation_rate: float = 0.2,
    neighbor_size: int | None = None,
    local_search_fraction: float = 0.3,
) -> Tuple[List[int], List[List[int]]]:
    """Evolve tours with a GA (exploration) and Lin-Kernighan local search
    (exploitation). Returns the best tour found along with a list of
    progressively better tours for logging.

    Parameters
    ----------
    dist_matrix : np.ndarray
        Symmetric distance matrix of shape (n, n).
    time_limit : float, optional
        Seconds available to the GA; `None` means run until convergence.
    seed : int, optional
        Random seed for reproducibility.
    population_size : int, default 60
        Number of individuals maintained each generation.
    elite_fraction : float, default 0.15
        Fraction of top-ranked individuals copied unchanged to the next gen.
    mutation_rate : float, default 0.2
        Probability of applying swap mutation to a child.
    neighbor_size : int, optional
        Size of candidate neighbor list for local search (default: min(25, n-1)).
    local_search_fraction : float, default 0.3
        Portion of the population refined with Lin-Kernighan per generation.
    """

    n = dist_matrix.shape[0]
    if n <= 1:
        tour = list(range(n))
        return tour, [tour]

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed % (2**32 - 1))

    neighbor_size = neighbor_size or min(25, n - 1)
    neighbor_size = max(1, min(neighbor_size, n - 1))
    neighbor_lists = np.argsort(dist_matrix, axis=1)[:, 1 : neighbor_size + 1]

    deadline = None if time_limit is None else time.time() + max(0.0, time_limit)

    population = _initial_population(dist_matrix, population_size)
    costs = [compute_cost(t, dist_matrix) for t in population]

    best_idx = int(np.argmin(costs))
    best_tour = population[best_idx][:]
    best_cost = float(costs[best_idx])
    progress: List[List[int]] = [best_tour[:]]

    elite_count = max(1, int(population_size * elite_fraction))
    local_search_count = max(1, int(population_size * local_search_fraction))
    tournament_k = max(2, min(6, population_size // 4))

    generation = 0
    while True:
        if deadline is not None and time.time() >= deadline:
            break

        generation += 1

        ranked = sorted(zip(costs, population), key=lambda x: x[0])
        elites = [ind[:] for _, ind in ranked[:elite_count]]

        new_population: List[List[int]] = elites[:]
        new_costs: List[float] = [compute_cost(ind, dist_matrix) for ind in elites]

        ls_applied = 0
        while len(new_population) < population_size:
            if deadline is not None and time.time() >= deadline:
                break

            parent1 = _tournament_select(population, costs, tournament_k)
            parent2 = _tournament_select(population, costs, tournament_k)
            child = _order_crossover(parent1, parent2)
            if random.random() < mutation_rate:
                _swap_mutation(child)

            # Local search (Lin-Kernighan) on a subset of children for exploitation
            if ls_applied < local_search_count:
                remaining = None if deadline is None else deadline - time.time()
                if remaining is None or remaining > 0.05:
                    ls_budget = None if remaining is None else min(remaining * 0.3, 1.0)
                    child = _lin_kernighan_refine(child, dist_matrix, neighbor_lists, ls_budget)
                    ls_applied += 1

            child_cost = compute_cost(child, dist_matrix)
            new_population.append(child)
            new_costs.append(child_cost)

            if child_cost + 1e-9 < best_cost:
                best_cost = child_cost
                best_tour = child[:]
                progress.append(child[:])

        population = new_population
        costs = new_costs

        # Optional diversification if stagnation detected
        if generation % 20 == 0:
            recent_best = min(costs)
            if abs(recent_best - best_cost) < 1e-6:
                population = _inject_diversity(population, dist_matrix, portion=0.2)
                costs = [compute_cost(t, dist_matrix) for t in population]

    if progress[-1] != best_tour:
        progress.append(best_tour[:])

    return best_tour, progress


# ---------------------------------------------------------------------------
# GA helpers
# ---------------------------------------------------------------------------


def _initial_population(dist_matrix: np.ndarray, population_size: int) -> List[List[int]]:
    n = dist_matrix.shape[0]
    population: List[List[int]] = []

    # Include one greedy seed
    start = random.randrange(n)
    greedy = _nearest_neighbor(dist_matrix, start)
    population.append(greedy)

    for _ in range(population_size - 1):
        tour = list(range(n))
        random.shuffle(tour)
        population.append(tour)

    return population


def _tournament_select(population: Sequence[List[int]], costs: Sequence[float], k: int) -> List[int]:
    best_idx = None
    for _ in range(k):
        idx = random.randrange(len(population))
        if best_idx is None or costs[idx] < costs[best_idx]:
            best_idx = idx
    return population[best_idx][:]


def _order_crossover(parent1: List[int], parent2: List[int]) -> List[int]:
    n = len(parent1)
    a, b = sorted(random.sample(range(n), 2))
    child = [-1] * n
    child[a:b+1] = parent1[a:b+1]

    inserted = set(child[a:b+1])
    pos = (b + 1) % n
    for idx in range(n):
        candidate = parent2[(b + 1 + idx) % n]
        if candidate in inserted:
            continue
        child[pos] = candidate
        inserted.add(candidate)
        pos = (pos + 1) % n

    return child


def _swap_mutation(tour: List[int]) -> None:
    if len(tour) < 2:
        return
    i, j = random.sample(range(len(tour)), 2)
    tour[i], tour[j] = tour[j], tour[i]


def _inject_diversity(population: List[List[int]], dist_matrix: np.ndarray, portion: float) -> List[List[int]]:
    n = len(population[0])
    replace_count = int(len(population) * portion)
    for idx in random.sample(range(len(population)), replace_count):
        tour = list(range(n))
        random.shuffle(tour)
        population[idx] = tour
    return population


# ---------------------------------------------------------------------------
# Lin-Kernighan style local search
# ---------------------------------------------------------------------------


def _lin_kernighan_refine(
    tour: List[int],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    time_limit: float | None,
) -> List[int]:
    start_time = time.time()
    deadline = None if time_limit is None else start_time + max(0.0, time_limit)

    current = tour[:]
    best = tour[:]
    best_cost = compute_cost(best, dist_matrix)

    while True:
        if deadline is not None and time.time() >= deadline:
            break

        improved, current = _best_2opt_improvement(current, dist_matrix, neighbor_lists)
        if improved:
            current_cost = compute_cost(current, dist_matrix)
            if current_cost + 1e-9 < best_cost:
                best = current[:]
                best_cost = current_cost
            continue

        # No improvement found: apply a double-bridge kick for diversification
        kicked = _double_bridge_move(best)
        if kicked == best:
            break
        current = kicked

    return best


def _best_2opt_improvement(
    tour: List[int], dist_matrix: np.ndarray, neighbor_lists: np.ndarray
) -> Tuple[bool, List[int]]:
    n = len(tour)
    best_delta = 0.0
    best_pair = None
    dm = dist_matrix

    positions = np.empty(n, dtype=int)
    for idx, city in enumerate(tour):
        positions[city] = idx

    for i in range(n):
        a = tour[i]
        b = tour[(i + 1) % n]
        for neighbor in neighbor_lists[a]:
            j = positions[int(neighbor)]
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
        return False, tour

    i, j = best_pair
    return True, _apply_2opt(tour, i, j)


def _nearest_neighbor(dist_matrix: np.ndarray, start: int = 0) -> List[int]:
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


def _apply_2opt(tour: List[int], i: int, j: int) -> List[int]:
    n = len(tour)
    if i == j:
        return tour[:]

    idxs = []
    cur = (i + 1) % n
    while True:
        idxs.append(cur)
        if cur == j:
            break
        cur = (cur + 1) % n

    if len(idxs) <= 1:
        return tour[:]

    new_tour = tour[:]
    segment = [tour[idx] for idx in idxs][::-1]
    for idx, node in zip(idxs, segment):
        new_tour[idx] = node
    return new_tour


def _double_bridge_move(tour: List[int]) -> List[int]:
    n = len(tour)
    if n < 8:
        shuffled = tour[:]
        random.shuffle(shuffled)
        return shuffled

    attempts = 0
    while attempts < 10:
        a, b, c, d = sorted(random.sample(range(n), 4))
        attempts += 1
        if a == 0 and d == n - 1:
            continue
        if b - a < 2 or c - b < 2 or d - c < 2:
            continue

        part1 = tour[:a]
        part2 = tour[a:b]
        part3 = tour[b:c]
        part4 = tour[c:d]
        part5 = tour[d:]
        new_tour = part1 + part4 + part2 + part3 + part5
        if len(new_tour) == n:
            return new_tour

    return tour[:]
