import multiprocessing as mp
import time
from multiprocessing.pool import Pool
# Use built-in generics (list/tuple/dict) instead of the typing module

import numpy as np

from utils import compute_cost, write_tour


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
    deadline: float | None,
) -> list[tuple[int, list[int], float]]:
    if not candidates:
        return []

    if deadline is not None and time.time() >= deadline:
        return []

    if pool is None:
        results: list[tuple[int, list[int], float]] = []
        for idx, tour, time_limit, seed in candidates:
            if deadline is not None and time.time() >= deadline:
                break
            rng = np.random.default_rng(seed)
            refined = _lin_kernighan_refine(tour, dist_matrix, neighbor_lists, time_limit, rng)
            cost = compute_cost(refined, dist_matrix)
            results.append((idx, refined, cost))
        return results

    jobs = [(idx, tour, time_limit, seed) for idx, tour, time_limit, seed in candidates]
    result_map: dict[int, tuple[list[int], float]] = {}
    try:
        for idx, refined, cost in pool.imap_unordered(_ls_worker, jobs, chunksize=1):
            result_map[idx] = (refined, cost)
            if deadline is not None and time.time() >= deadline:
                break
    except KeyboardInterrupt:
        pool.terminate()
        raise

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
    ants: int = 40,
    alpha: float = 1.0,
    beta: float = 3.0,
    rho: float = 0.1,
    q0: float = 0.9,
    neighbor_size: int | None = None,
    local_search_fraction: float = 0.5,
    output_file: str | None = None,
) -> tuple[list[int], list[list[int]]]:
    """Ant Colony Optimization (ACO) hybridized with Lin-Kernighan (LK) local search.

    This replaces the previous GA. It keeps the external API name so `main.py`
    can call it without changes. The algorithm constructs ant tours using
    pheromones and a candidate list, applies LK to a fraction of constructed
    tours in parallel, and updates pheromones using the best solutions found.

    Returns the best tour and a progress list of improving tours (for logging).
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

    # Pheromone matrix (symmetric) initialized to a small positive value
    tau0 = 1.0 / (n * np.mean(dist_matrix))
    pheromone = np.full((n, n), tau0, dtype=float)

    # Seed with a deterministic tour so we always have an initial solution.
    initial_tour = _nearest_neighbor(dist_matrix, 0)
    initial_cost = compute_cost(initial_tour, dist_matrix)

    best_tour: list[int] | None = initial_tour[:]
    best_cost = float(initial_cost)
    progress: list[list[int]] = [initial_tour[:]]

    if output_file is not None:
        try:
            write_tour(output_file, initial_tour)
        except Exception:
            # Ignore I/O errors and continue solving.
            pass

    ants = max(1, int(ants))
    ls_count = max(1, int(ants * local_search_fraction))

    ctx = mp.get_context("spawn")
    ls_pool: Pool | None = None
    ls_worker_count = min(ls_count, max(1, ctx.cpu_count() or 1))
    if ls_worker_count > 1:
        ls_pool = ctx.Pool(
            processes=ls_worker_count,
            initializer=_ls_worker_init,
            initargs=(dist_matrix, neighbor_lists),
        )

    timed_out = False
    interrupted = False

    try:
        iteration = 0
        while True:
            if deadline is not None and time.time() >= deadline:
                timed_out = True
                break

            iteration += 1
            constructed: list[tuple[int, list[int], float]] = []
            for a in range(ants):
                if deadline is not None and time.time() >= deadline:
                    timed_out = True
                    break
                seed_a = int(rng.integers(0, 2**63, dtype=np.int64))
                tour = _construct_ant_tour(
                    dist_matrix,
                    pheromone,
                    neighbor_lists,
                    alpha,
                    beta,
                    q0,
                    seed_a,
                )
                cost = compute_cost(tour, dist_matrix)
                constructed.append((a, tour, cost))

            if not constructed:
                break

            # Sort by ant index to stabilize ordering
            constructed.sort(key=lambda x: x[0])

            # Apply LK to top ls_count ants (by cost) in parallel
            constructed_sorted = sorted(constructed, key=lambda x: x[2])
            ls_candidates: list[tuple[int, list[int], float | None, int]] = []
            for pos, (ant_idx, tour, cost) in enumerate(constructed_sorted[:ls_count]):
                if deadline is not None and time.time() >= deadline:
                    break
                ls_seed = int(rng.integers(0, 2**63, dtype=np.int64))
                remaining = None if deadline is None else max(0.0, deadline - time.time())
                ls_budget = None
                if remaining is not None and remaining > 0.02:
                    ls_budget = min(max(remaining * 0.3, 0.05), 1.5)
                ls_candidates.append((ant_idx, tour[:], ls_budget, ls_seed))

            refined_results: list[tuple[int, list[int], float]] = []
            if ls_candidates:
                refined_results = _run_parallel_ls(
                    ls_candidates,
                    dist_matrix,
                    neighbor_lists,
                    ls_pool,
                    deadline,
                )

            # Merge refined results back into constructed list
            refined_map = {idx: (tour, cost) for idx, tour, cost in refined_results}
            final_solutions: list[tuple[int, list[int], float]] = []
            for idx, tour, cost in constructed:
                if idx in refined_map:
                    tour_ref, c_ref = refined_map[idx]
                    final_solutions.append((idx, tour_ref, c_ref))
                else:
                    final_solutions.append((idx, tour, cost))

            if deadline is not None and time.time() >= deadline:
                timed_out = True
                break

            # Find best ant this iteration
            for _, tour, cost in final_solutions:
                if cost + 1e-12 < best_cost:
                    best_cost = cost
                    best_tour = tour[:]
                    progress.append(best_tour[:])
                    # write immediately so main process / output file shows progress
                    try:
                        if output_file is not None:
                            write_tour(output_file, best_tour)
                    except Exception:
                        # Do not crash the solver if writing fails; continue
                        pass

            # Pheromone evaporation
            pheromone *= (1.0 - rho)

            # Pheromone deposit: best ant of this iteration (or global best)
            iter_best = min(final_solutions, key=lambda x: x[2])
            best_to_deposit = iter_best[1]
            deposit_cost = float(iter_best[2])
            if best_tour is not None and best_cost < deposit_cost:
                best_to_deposit = best_tour
                deposit_cost = best_cost

            # Add pheromone along tour edges
            delta = 1.0 / max(1e-9, deposit_cost)
            n_nodes = len(best_to_deposit)
            for i in range(n_nodes):
                a = best_to_deposit[i]
                b = best_to_deposit[(i + 1) % n_nodes]
                pheromone[a, b] += delta
                pheromone[b, a] += delta

            # Optional pheromone bounding to avoid numerical issues
            pheromone = np.clip(pheromone, 1e-12, 1e12)

            # Stopping check by deadline is at loop top; continue iterations until time runs out
            if deadline is not None and time.time() >= deadline:
                timed_out = True
                break
    except KeyboardInterrupt:
        interrupted = True
        timed_out = True
    finally:
        if ls_pool is not None:
            try:
                if timed_out:
                    ls_pool.terminate()
                else:
                    ls_pool.close()
            finally:
                ls_pool.join()

    # Ensure the last progress element is global best
    if not progress or progress[-1] != best_tour:
        progress.append(best_tour[:])

    if interrupted:
        raise KeyboardInterrupt

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


def _construct_ant_tour(
    dist_matrix: np.ndarray,
    pheromone: np.ndarray,
    neighbor_lists: np.ndarray,
    alpha: float,
    beta: float,
    q0: float,
    seed: int,
) -> list[int]:
    rng = np.random.default_rng(seed)
    n = dist_matrix.shape[0]

    visited = np.zeros(n, dtype=bool)
    tour: list[int] = []
    current = int(rng.integers(n))
    tour.append(current)
    visited[current] = True

    for _ in range(n - 1):
        # candidate list: neighbors of current not yet visited
        cand = [int(c) for c in neighbor_lists[current] if not visited[int(c)]]
        if not cand:
            # fallback to all unvisited
            cand = [int(i) for i in range(n) if not visited[i]]

        # compute desirability: tau^alpha * (1/d)^beta
        taus = np.array([pheromone[current, c] for c in cand], dtype=float)
        with np.errstate(divide='ignore'):
            heur = np.array([1.0 / (dist_matrix[current, c] + 1e-12) for c in cand], dtype=float)
        scores = (taus ** alpha) * (heur ** beta)

        # pseudo-random proportional rule (q0 greedy)
        if float(rng.random()) < q0:
            choice_idx = int(np.argmax(scores))
        else:
            total = scores.sum()
            if total <= 0 or np.isfinite(total) and total == 0:
                choice_idx = int(rng.integers(len(cand)))
            else:
                probs = scores / total
                # choose according to probabilities
                choice_idx = int(rng.choice(len(cand), p=probs))

        nxt = cand[choice_idx]
        tour.append(int(nxt))
        visited[nxt] = True
        current = int(nxt)

    return tour
