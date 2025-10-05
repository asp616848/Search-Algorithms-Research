import multiprocessing as mp
import time
from multiprocessing.pool import Pool
# Use built-in generics (list/tuple/dict) instead of the typing module

import numpy as np

from utils import compute_cost


_LS_DIST_MATRIX: np.ndarray | None = None
_LS_NEIGHBOR_LISTS: np.ndarray | None = None


def _compute_population_costs(
    population: list[list[int]],
    dist_matrix: np.ndarray,
) -> np.ndarray:
    if not population:
        return np.empty(0, dtype=float)

    tours = np.asarray(population, dtype=int)
    if tours.ndim == 1:
        tours = tours.reshape(1, -1)

    next_nodes = np.roll(tours, -1, axis=1)
    costs = dist_matrix[tours, next_nodes].sum(axis=1)
    return costs.astype(float)


def _ls_worker_init(dist_matrix: np.ndarray, neighbor_lists: np.ndarray) -> None:
    global _LS_DIST_MATRIX, _LS_NEIGHBOR_LISTS
    _LS_DIST_MATRIX = dist_matrix
    _LS_NEIGHBOR_LISTS = neighbor_lists


def _ls_worker(job: tuple[int, list[int], float | None, int]) -> tuple[int, list[int], float]:
    idx, tour, time_limit, seed = job
    assert _LS_DIST_MATRIX is not None and _LS_NEIGHBOR_LISTS is not None
    rng = np.random.default_rng(seed)
    refined = _lin_kernighan_refine(tour, _LS_DIST_MATRIX, _LS_NEIGHBOR_LISTS, time_limit, rng)
    cost = compute_cost(refined, _LS_DIST_MATRIX)
    return idx, refined, cost


def _run_parallel_ls(
    candidates: list[tuple[int, list[int], float | None, int]],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    pool: Pool | None,
) -> list[tuple[int, list[int], float]]:
    if not candidates:
        return []

    if pool is None:
        results: list[tuple[int, list[int], float]] = []
        for idx, tour, time_limit, seed in candidates:
            rng = np.random.default_rng(seed)
            refined = _lin_kernighan_refine(tour, dist_matrix, neighbor_lists, time_limit, rng)
            cost = compute_cost(refined, dist_matrix)
            results.append((idx, refined, cost))
        return results

    jobs = [(idx, tour, time_limit, seed) for idx, tour, time_limit, seed in candidates]
    result_map: dict[int, tuple[list[int], float]] = {}
    for idx, refined, cost in pool.imap_unordered(_ls_worker, jobs, chunksize=1):
        result_map[idx] = (refined, cost)

    ordered: list[tuple[int, list[int], float]] = []
    for idx, _, _, _ in candidates:
        refined, cost = result_map[idx]
        ordered.append((idx, refined, cost))
    return ordered


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
) -> tuple[list[int], list[list[int]]]:
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

    rng = np.random.default_rng(seed)

    neighbor_size = neighbor_size or min(25, n - 1)
    neighbor_size = max(1, min(neighbor_size, n - 1))
    neighbor_lists = np.argsort(dist_matrix, axis=1)[:, 1 : neighbor_size + 1]

    deadline = None if time_limit is None else time.time() + max(0.0, time_limit)

    population = _initial_population(dist_matrix, population_size, rng)
    costs = _compute_population_costs(population, dist_matrix).tolist()

    best_idx = int(np.argmin(costs))
    best_tour = population[best_idx][:]
    best_cost = float(costs[best_idx])
    progress: list[list[int]] = [best_tour[:]]

    elite_count = max(1, int(population_size * elite_fraction))
    local_search_count = max(1, int(population_size * local_search_fraction))
    tournament_k = max(2, min(6, population_size // 4))

    ctx = mp.get_context("spawn")
    ls_pool: Pool | None = None
    ls_worker_count = min(local_search_count, max(1, ctx.cpu_count() or 1))
    if ls_worker_count > 1:
        ls_pool = ctx.Pool(
            processes=ls_worker_count,
            initializer=_ls_worker_init,
            initargs=(dist_matrix, neighbor_lists),
        )

    try:
        generation = 0
        while True:
            if deadline is not None and time.time() >= deadline:
                break

            generation += 1

            ranked = sorted(zip(costs, population), key=lambda x: x[0])
            elites = [ind[:] for _, ind in ranked[:elite_count]]

            new_population: list[list[int]] = elites[:]
            new_costs = _compute_population_costs(elites, dist_matrix).tolist()

            ls_applied = 0
            ls_candidates: list[tuple[int, list[int], float | None, int]] = []

            while len(new_population) < population_size:
                if deadline is not None and time.time() >= deadline:
                    break

                parent1 = _tournament_select(population, costs, tournament_k, rng)
                parent2 = _tournament_select(population, costs, tournament_k, rng)
                child = _order_crossover(parent1, parent2, rng)
                if float(rng.random()) < mutation_rate:
                    _swap_mutation(child, rng)

                idx = len(new_population)
                new_population.append(child)

                if ls_applied < local_search_count:
                    remaining = None if deadline is None else max(0.0, deadline - time.time())
                    if remaining is None or remaining > 0.05:
                        ls_budget = None if remaining is None else min(remaining * 0.3, 1.0)
                        ls_seed = int(rng.integers(0, 2**63, dtype=np.int64))
                        ls_candidates.append((idx, child[:], ls_budget, ls_seed))
                        new_costs.append(float("inf"))
                        ls_applied += 1
                        continue

                child_cost = compute_cost(child, dist_matrix)
                new_costs.append(child_cost)
                if child_cost + 1e-9 < best_cost:
                    best_cost = child_cost
                    best_tour = child[:]
                    progress.append(child[:])

            if ls_candidates:
                refined = _run_parallel_ls(
                    ls_candidates,
                    dist_matrix,
                    neighbor_lists,
                    ls_pool,
                )
                for idx, tour_refined, refined_cost in refined:
                    new_population[idx] = tour_refined
                    new_costs[idx] = refined_cost
                    if refined_cost + 1e-9 < best_cost:
                        best_cost = refined_cost
                        best_tour = tour_refined[:]
                        progress.append(tour_refined[:])

            population = new_population
            costs = new_costs

            # Optional diversification if stagnation detected
            if generation % 20 == 0:
                recent_best = min(costs)
                if abs(recent_best - best_cost) < 1e-6:
                    population = _inject_diversity(population, dist_matrix, portion=0.2, rng=rng)
                    costs = _compute_population_costs(population, dist_matrix).tolist()
    finally:
        if ls_pool is not None:
            ls_pool.close()
            ls_pool.join()

    if progress[-1] != best_tour:
        progress.append(best_tour[:])

    return best_tour, progress


# ---------------------------------------------------------------------------
# GA helpers
# ---------------------------------------------------------------------------


def _initial_population(
    dist_matrix: np.ndarray, population_size: int, rng: np.random.Generator
) -> list[list[int]]:
    n = dist_matrix.shape[0]
    population: list[list[int]] = []

    # Include one greedy seed
    start = int(rng.integers(n))
    greedy = _nearest_neighbor(dist_matrix, start)
    population.append(greedy)

    for _ in range(population_size - 1):
        population.append(rng.permutation(n).tolist())

    return population


def _tournament_select(
    population: list[list[int]],
    costs: list[float],
    k: int,
    rng: np.random.Generator,
) -> list[int]:
    best_idx = None
    for _ in range(k):
        idx = int(rng.integers(len(population)))
        if best_idx is None or costs[idx] < costs[best_idx]:
            best_idx = idx
    return population[best_idx][:]


def _order_crossover(
    parent1: list[int], parent2: list[int], rng: np.random.Generator
) -> list[int]:
    n = len(parent1)
    a, b = sorted(int(x) for x in rng.choice(n, size=2, replace=False))
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


def _swap_mutation(tour: list[int], rng: np.random.Generator) -> None:
    if len(tour) < 2:
        return
    i, j = rng.choice(len(tour), size=2, replace=False)
    i = int(i)
    j = int(j)
    tour[i], tour[j] = tour[j], tour[i]


def _inject_diversity(
    population: list[list[int]],
    dist_matrix: np.ndarray,
    portion: float,
    rng: np.random.Generator,
) -> list[list[int]]:
    n = len(population[0])
    replace_count = int(len(population) * portion)
    if replace_count <= 0:
        return population

    selected = rng.choice(len(population), size=replace_count, replace=False)
    for idx in selected:
        population[int(idx)] = rng.permutation(n).tolist()
    return population


# ---------------------------------------------------------------------------
# Lin-Kernighan style local search
# ---------------------------------------------------------------------------


def _lin_kernighan_refine(
    tour: list[int],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    time_limit: float | None,
    rng: np.random.Generator,
) -> list[int]:
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
        kicked = _double_bridge_move(best, rng)
        if kicked == best:
            break
        current = kicked

    return best


def _best_2opt_improvement(
    tour: list[int], dist_matrix: np.ndarray, neighbor_lists: np.ndarray
) -> tuple[bool, list[int]]:
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


def _nearest_neighbor(dist_matrix: np.ndarray, start: int = 0) -> list[int]:
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


def _apply_2opt(tour: list[int], i: int, j: int) -> list[int]:
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


def _double_bridge_move(tour: list[int], rng: np.random.Generator) -> list[int]:
    n = len(tour)
    if n < 8:
        return rng.permutation(tour).tolist()

    attempts = 0
    while attempts < 10:
        a, b, c, d = sorted(int(x) for x in rng.choice(n, size=4, replace=False))
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
