import multiprocessing as mp
import time
from multiprocessing.pool import Pool
import sys

import numpy as np

from utils import compute_cost, write_tour


_LS_DIST_MATRIX: np.ndarray | None = None
_LS_NEIGHBOR_LISTS: np.ndarray | None = None


def _ls_worker_init(dist_matrix: np.ndarray, neighbor_lists: np.ndarray) -> None:
    global _LS_DIST_MATRIX, _LS_NEIGHBOR_LISTS
    _LS_DIST_MATRIX = dist_matrix
    _LS_NEIGHBOR_LISTS = neighbor_lists


def _ls_worker(job: tuple[int, list[int], float | None, int]) -> tuple[int, list[int], float]:
    idx, tour, time_limit, seed = job
    assert _LS_DIST_MATRIX is not None and _LS_NEIGHBOR_LISTS is not None
    rng = np.random.default_rng(seed)
    refined = _local_search_refine(tour, _LS_DIST_MATRIX, _LS_NEIGHBOR_LISTS, time_limit, rng)
    cost = compute_cost(refined, _LS_DIST_MATRIX)
    return idx, refined, cost


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
    """Hybrid Held-Karp algorithm that continuously improves until termination.
    
    Uses exact DP for small instances and multi-strategy iterative improvement
    for larger instances. Keeps searching for better solutions until time runs out.
    
    Returns the best tour and a progress list of improving tours.
    """
    
    n = dist_matrix.shape[0]
    if n <= 1:
        tour = list(range(n))
        return tour, [tour]
    
    rng = np.random.default_rng(seed)
    deadline = None if time_limit is None else time.time() + max(0.0, time_limit)
    
    neighbor_size = neighbor_size or min(25, n - 1)
    neighbor_size = max(1, min(neighbor_size, n - 1))
    neighbor_lists = np.argsort(dist_matrix, axis=1)[:, 1 : neighbor_size + 1]
    
    # For very small problems, use exact Held-Karp
    if n <= 18:
        return _held_karp_exact(dist_matrix, deadline, output_file)
    
    # For larger problems, use continuous improvement strategy
    return _continuous_improvement(
        dist_matrix, 
        neighbor_lists, 
        deadline, 
        output_file, 
        rng
    )


def _held_karp_exact(
    dist_matrix: np.ndarray,
    deadline: float | None,
    output_file: str | None,
) -> tuple[list[int], list[list[int]]]:
    """Exact Held-Karp algorithm for small TSP instances."""
    
    n = dist_matrix.shape[0]
    
    # Initialize with nearest neighbor heuristic
    initial_tour = _nearest_neighbor(dist_matrix, 0)
    best_tour = initial_tour[:]
    best_cost = compute_cost(initial_tour, dist_matrix)
    progress = [initial_tour[:]]
    
    if output_file is not None:
        try:
            write_tour(output_file, initial_tour)
        except Exception:
            pass
    
    # DP table: dp[mask][i] = minimum cost to visit cities in mask, ending at i
    dp = {}
    parent = {}
    
    # Base case: starting from city 0
    dp[(1 << 0, 0)] = 0.0
    
    # Build up subsets of increasing size
    for subset_size in range(2, n + 1):
        if deadline is not None and time.time() >= deadline:
            break
        
        for mask in range(1 << n):
            if bin(mask).count('1') != subset_size:
                continue
            if not (mask & (1 << 0)):
                continue
            
            for last in range(n):
                if not (mask & (1 << last)):
                    continue
                
                prev_mask = mask ^ (1 << last)
                min_cost = float('inf')
                best_prev = -1
                
                for prev in range(n):
                    if not (prev_mask & (1 << prev)):
                        continue
                    if (prev_mask, prev) not in dp:
                        continue
                    
                    cost = dp[(prev_mask, prev)] + dist_matrix[prev, last]
                    if cost < min_cost:
                        min_cost = cost
                        best_prev = prev
                
                if best_prev != -1:
                    dp[(mask, last)] = min_cost
                    parent[(mask, last)] = best_prev
    
    # Find minimum cost tour
    full_mask = (1 << n) - 1
    min_tour_cost = float('inf')
    best_last = -1
    
    for last in range(1, n):
        if (full_mask, last) not in dp:
            continue
        cost = dp[(full_mask, last)] + dist_matrix[last, 0]
        if cost < min_tour_cost:
            min_tour_cost = cost
            best_last = last
    
    # Reconstruct tour
    if best_last != -1 and min_tour_cost < best_cost:
        tour = []
        mask = full_mask
        current = best_last
        
        while mask != 0:
            tour.append(current)
            if (mask, current) in parent:
                next_city = parent[(mask, current)]
                mask ^= (1 << current)
                current = next_city
            else:
                break
        
        tour.reverse()
        best_tour = tour
        best_cost = min_tour_cost
        progress.append(best_tour[:])
        
        if output_file is not None:
            try:
                write_tour(output_file, best_tour)
            except Exception:
                pass
    
    return best_tour, progress


def _continuous_improvement(
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    deadline: float | None,
    output_file: str | None,
    rng: np.random.Generator,
) -> tuple[list[int], list[list[int]]]:
    """Continuously improve tour until time runs out using multiple strategies."""
    
    n = dist_matrix.shape[0]
    
    # Phase 1: Generate initial solution pool
    initial_pool = _generate_initial_pool(dist_matrix, neighbor_lists, n, rng, deadline)
    
    best_tour = initial_pool[0]
    best_cost = compute_cost(best_tour, dist_matrix)
    progress = [best_tour[:]]
    
    if output_file is not None:
        try:
            write_tour(output_file, best_tour)
        except Exception:
            pass
    
    # Setup parallel processing
    ctx = mp.get_context("spawn")
    num_workers = min(4, max(1, ctx.cpu_count() or 1))
    pool: Pool | None = None
    
    if num_workers > 1:
        try:
            pool = ctx.Pool(
                processes=num_workers,
                initializer=_ls_worker_init,
                initargs=(dist_matrix, neighbor_lists),
            )
        except Exception:
            pool = None
    
    try:
        # Phase 2: Continuous improvement loop
        iteration = 0
        no_improvement_count = 0
        current_solutions = initial_pool[:min(10, len(initial_pool))]
        
        while True:
            if deadline is not None and time.time() >= deadline:
                break
            
            iteration += 1
            improved_this_round = False
            
            # Strategy 1: Parallel local search on current solutions
            if iteration % 3 == 0:
                jobs = []
                for idx, tour in enumerate(current_solutions[:5]):
                    if deadline is not None and time.time() >= deadline:
                        break
                    remaining = None if deadline is None else max(0.0, deadline - time.time())
                    time_budget = min(2.0, remaining * 0.1) if remaining else 2.0
                    seed_val = int(rng.integers(0, 2**63, dtype=np.int64))
                    jobs.append((idx, tour[:], time_budget, seed_val))
                
                if jobs:
                    if pool:
                        try:
                            results = []
                            for result in pool.imap_unordered(_ls_worker, jobs, chunksize=1):
                                results.append(result)
                                if deadline is not None and time.time() >= deadline:
                                    break
                        except Exception:
                            results = []
                    else:
                        results = []
                        for job in jobs:
                            results.append(_ls_worker(job))
                    
                    for idx, refined, cost in results:
                        if cost < best_cost - 1e-9:
                            best_cost = cost
                            best_tour = refined[:]
                            progress.append(best_tour[:])
                            improved_this_round = True
                            
                            if output_file is not None:
                                try:
                                    write_tour(output_file, best_tour)
                                except Exception:
                                    pass
                        
                        current_solutions[idx] = refined[:]
            
            # Strategy 2: Aggressive 2-opt on best solution
            if iteration % 2 == 0:
                improved, new_tour = _best_2opt_improvement(
                    best_tour, dist_matrix, neighbor_lists
                )
                if improved:
                    new_cost = compute_cost(new_tour, dist_matrix)
                    if new_cost < best_cost - 1e-9:
                        best_cost = new_cost
                        best_tour = new_tour[:]
                        progress.append(best_tour[:])
                        improved_this_round = True
                        
                        if output_file is not None:
                            try:
                                write_tour(output_file, best_tour)
                            except Exception:
                                pass
            
            # Strategy 3: 3-opt moves
            if iteration % 5 == 0:
                improved_3opt = _apply_3opt_moves(
                    best_tour, dist_matrix, rng, deadline
                )
                if improved_3opt != best_tour:
                    new_cost = compute_cost(improved_3opt, dist_matrix)
                    if new_cost < best_cost - 1e-9:
                        best_cost = new_cost
                        best_tour = improved_3opt[:]
                        progress.append(best_tour[:])
                        improved_this_round = True
                        
                        if output_file is not None:
                            try:
                                write_tour(output_file, best_tour)
                            except Exception:
                                pass
            
            # Strategy 4: Or-opt moves (relocate sequences)
            if iteration % 4 == 0:
                improved_or = _or_opt_search(best_tour, dist_matrix, deadline)
                if improved_or != best_tour:
                    new_cost = compute_cost(improved_or, dist_matrix)
                    if new_cost < best_cost - 1e-9:
                        best_cost = new_cost
                        best_tour = improved_or[:]
                        progress.append(best_tour[:])
                        improved_this_round = True
                        
                        if output_file is not None:
                            try:
                                write_tour(output_file, best_tour)
                            except Exception:
                                pass
            
            # Strategy 5: Generate new candidates with perturbations
            if iteration % 10 == 0 or no_improvement_count > 5:
                new_candidates = _generate_perturbed_solutions(
                    best_tour, dist_matrix, neighbor_lists, rng, 3
                )
                current_solutions = [best_tour[:]] + new_candidates
                no_improvement_count = 0
            
            # Strategy 6: Reconstruct with savings algorithm
            if iteration % 20 == 0:
                savings_tour = _savings_algorithm(dist_matrix, rng)
                savings_cost = compute_cost(savings_tour, dist_matrix)
                if savings_cost < best_cost - 1e-9:
                    best_cost = savings_cost
                    best_tour = savings_tour[:]
                    progress.append(best_tour[:])
                    improved_this_round = True
                    
                    if output_file is not None:
                        try:
                            write_tour(output_file, best_tour)
                        except Exception:
                            pass
            
            if improved_this_round:
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # Never stop - keep trying new strategies until time runs out
            if deadline is not None and time.time() >= deadline:
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        if pool is not None:
            try:
                pool.terminate()
            finally:
                pool.join()
    
    if not progress or progress[-1] != best_tour:
        progress.append(best_tour[:])
    
    return best_tour, progress


def _generate_initial_pool(
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    n: int,
    rng: np.random.Generator,
    deadline: float | None,
) -> list[list[int]]:
    """Generate diverse initial solution pool."""
    pool = []
    
    # Nearest neighbor from multiple starts
    for start in range(min(n, 15)):
        if deadline is not None and time.time() >= deadline:
            break
        tour = _nearest_neighbor(dist_matrix, start)
        pool.append(tour)
    
    # Farthest insertion
    if deadline is None or time.time() < deadline:
        pool.append(_farthest_insertion(dist_matrix))
    
    # Random tours with quick 2-opt
    for _ in range(5):
        if deadline is not None and time.time() >= deadline:
            break
        tour = rng.permutation(n).tolist()
        tour = _quick_2opt(tour, dist_matrix, neighbor_lists, 0.1)
        pool.append(tour)
    
    # Sort by cost
    costs = [compute_cost(t, dist_matrix) for t in pool]
    pool = [t for _, t in sorted(zip(costs, pool))]
    
    return pool


def _local_search_refine(
    tour: list[int],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    time_limit: float | None,
    rng: np.random.Generator,
) -> list[int]:
    """Intensive local search with multiple operators."""
    start_time = time.time()
    deadline = None if time_limit is None else start_time + max(0.0, time_limit)
    
    current = tour[:]
    best = tour[:]
    best_cost = compute_cost(best, dist_matrix)
    
    while True:
        if deadline is not None and time.time() >= deadline:
            break
        
        # 2-opt
        improved, current = _best_2opt_improvement(current, dist_matrix, neighbor_lists)
        if improved:
            cost = compute_cost(current, dist_matrix)
            if cost < best_cost - 1e-9:
                best = current[:]
                best_cost = cost
            continue
        
        # Or-opt
        improved_or = _or_opt_search(current, dist_matrix, deadline)
        if improved_or != current:
            cost = compute_cost(improved_or, dist_matrix)
            if cost < best_cost - 1e-9:
                best = improved_or[:]
                best_cost = cost
                current = improved_or[:]
                continue
        
        # Kick with double-bridge
        kicked = _double_bridge_move(best, rng)
        if kicked == best:
            break
        current = kicked
    
    return best


def _best_2opt_improvement(
    tour: list[int], 
    dist_matrix: np.ndarray, 
    neighbor_lists: np.ndarray
) -> tuple[bool, list[int]]:
    """Find best 2-opt improvement using neighbor lists."""
    n = len(tour)
    best_delta = 0.0
    best_pair = None
    
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
            
            delta = dist_matrix[a, c] + dist_matrix[b, d] - dist_matrix[a, b] - dist_matrix[c, d]
            if delta < best_delta - 1e-12:
                best_delta = delta
                best_pair = (i, j)
    
    if best_pair is None:
        return False, tour
    
    i, j = best_pair
    return True, _apply_2opt(tour, i, j)


def _apply_2opt(tour: list[int], i: int, j: int) -> list[int]:
    """Apply 2-opt swap."""
    n = len(tour)
    if i == j:
        return tour[:]
    
    new_tour = tour[:]
    if i < j:
        new_tour[i+1:j+1] = reversed(tour[i+1:j+1])
    else:
        new_tour[j+1:i+1] = reversed(tour[j+1:i+1])
    
    return new_tour


def _apply_3opt_moves(
    tour: list[int],
    dist_matrix: np.ndarray,
    rng: np.random.Generator,
    deadline: float | None,
) -> list[int]:
    """Apply 3-opt moves to tour."""
    n = len(tour)
    best_tour = tour[:]
    best_cost = compute_cost(tour, dist_matrix)
    
    # Try systematic 3-opt on subset
    sample_size = min(30, n)
    for _ in range(5):
        if deadline is not None and time.time() >= deadline:
            break
        
        indices = sorted(rng.choice(n, size=3, replace=False))
        i, j, k = indices
        
        # All 3-opt reconnections
        reconnections = _get_3opt_reconnections(tour, i, j, k)
        
        for new_tour in reconnections:
            cost = compute_cost(new_tour, dist_matrix)
            if cost < best_cost - 1e-9:
                best_cost = cost
                best_tour = new_tour[:]
    
    return best_tour


def _get_3opt_reconnections(tour: list[int], i: int, j: int, k: int) -> list[list[int]]:
    """Generate all 3-opt reconnections."""
    a, b, c = tour[:i], tour[i:j], tour[j:k]
    d = tour[k:]
    
    return [
        a + b + c + d,
        a + b[::-1] + c + d,
        a + b + c[::-1] + d,
        a + c + b + d,
        a + c[::-1] + b[::-1] + d,
        a + c + b[::-1] + d,
        a + c[::-1] + b + d,
    ]


def _or_opt_search(
    tour: list[int],
    dist_matrix: np.ndarray,
    deadline: float | None,
) -> list[int]:
    """Or-opt: relocate sequences of 1, 2, or 3 cities."""
    n = len(tour)
    best_tour = tour[:]
    best_cost = compute_cost(tour, dist_matrix)
    
    for length in [1, 2, 3]:
        if deadline is not None and time.time() >= deadline:
            break
        
        for i in range(n):
            if deadline is not None and time.time() >= deadline:
                break
            
            for j in range(n):
                if abs(i - j) <= length:
                    continue
                
                # Extract segment and insert at new position
                segment = tour[i:i+length] if i+length <= n else tour[i:] + tour[:((i+length) % n)]
                remaining = tour[:i] + tour[i+length:] if i+length <= n else tour[(i+length) % n:i]
                
                new_tour = remaining[:j] + segment + remaining[j:]
                if len(new_tour) != n:
                    continue
                
                cost = compute_cost(new_tour, dist_matrix)
                if cost < best_cost - 1e-9:
                    best_cost = cost
                    best_tour = new_tour[:]
    
    return best_tour


def _generate_perturbed_solutions(
    tour: list[int],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    rng: np.random.Generator,
    count: int,
) -> list[list[int]]:
    """Generate perturbed solutions from current best."""
    solutions = []
    
    for _ in range(count):
        # Apply random perturbation
        perturbed = _double_bridge_move(tour, rng)
        # Quick refinement
        refined = _quick_2opt(perturbed, dist_matrix, neighbor_lists, 0.2)
        solutions.append(refined)
    
    return solutions


def _quick_2opt(
    tour: list[int],
    dist_matrix: np.ndarray,
    neighbor_lists: np.ndarray,
    time_budget: float,
) -> list[int]:
    """Quick 2-opt with time limit."""
    start = time.time()
    current = tour[:]
    
    while time.time() - start < time_budget:
        improved, current = _best_2opt_improvement(current, dist_matrix, neighbor_lists)
        if not improved:
            break
    
    return current


def _nearest_neighbor(dist_matrix: np.ndarray, start: int = 0) -> list[int]:
    """Nearest neighbor construction heuristic."""
    n = dist_matrix.shape[0]
    unvisited = np.ones(n, dtype=bool)
    tour = [int(start)]
    unvisited[start] = False
    last = start
    
    while unvisited.any():
        dists = dist_matrix[last].copy()
        dists[~unvisited] = np.inf
        next_city = int(np.argmin(dists))
        tour.append(next_city)
        unvisited[next_city] = False
        last = next_city
    
    return tour


def _farthest_insertion(dist_matrix: np.ndarray) -> list[int]:
    """Farthest insertion construction heuristic."""
    n = dist_matrix.shape[0]
    tour = [0]
    unvisited = set(range(1, n))
    
    # Find farthest from 0
    farthest = int(np.argmax(dist_matrix[0, 1:]))
    tour.append(farthest + 1)
    unvisited.remove(farthest + 1)
    
    while unvisited:
        # Find farthest city from tour
        max_dist = -1
        farthest_city = None
        
        for city in unvisited:
            min_dist = min(dist_matrix[city, t] for t in tour)
            if min_dist > max_dist:
                max_dist = min_dist
                farthest_city = city
        
        # Find best insertion position
        best_pos = 0
        best_cost = float('inf')
        
        for i in range(len(tour)):
            a, b = tour[i], tour[(i + 1) % len(tour)]
            cost = dist_matrix[a, farthest_city] + dist_matrix[farthest_city, b] - dist_matrix[a, b]
            if cost < best_cost:
                best_cost = cost
                best_pos = i + 1
        
        tour.insert(best_pos, farthest_city)
        unvisited.remove(farthest_city)
    
    return tour


def _savings_algorithm(dist_matrix: np.ndarray, rng: np.random.Generator) -> list[int]:
    """Clarke-Wright savings algorithm."""
    n = dist_matrix.shape[0]
    depot = int(rng.integers(n))
    
    # Calculate savings
    savings = []
    for i in range(n):
        for j in range(i + 1, n):
            if i == depot or j == depot:
                continue
            s = dist_matrix[depot, i] + dist_matrix[depot, j] - dist_matrix[i, j]
            savings.append((s, i, j))
    
    savings.sort(reverse=True)
    
    # Build routes
    routes = {i: [i] for i in range(n) if i != depot}
    
    for s, i, j in savings:
        route_i = None
        route_j = None
        
        for key, route in routes.items():
            if i in route:
                route_i = key
            if j in route:
                route_j = key
        
        if route_i and route_j and route_i != route_j:
            # Merge routes
            if routes[route_i][-1] == i and routes[route_j][0] == j:
                routes[route_i].extend(routes[route_j])
                del routes[route_j]
            elif routes[route_i][0] == i and routes[route_j][-1] == j:
                routes[route_j].extend(routes[route_i])
                del routes[route_i]
    
    # Combine all routes into tour
    tour = [depot]
    for route in routes.values():
        tour.extend(route)
    
    return tour[:n]


def _double_bridge_move(tour: list[int], rng: np.random.Generator) -> list[int]:
    """Double-bridge perturbation move."""
    n = len(tour)
    if n < 8:
        return tour[:]
    
    for _ in range(10):
        indices = sorted(rng.choice(n, size=4, replace=False))
        a, b, c, d = indices
        
        if b - a < 2 or c - b < 2 or d - c < 2:
            continue
        
        new_tour = tour[:a] + tour[c:d] + tour[b:c] + tour[a:b] + tour[d:]
        if len(new_tour) == n:
            return new_tour
    
    return tour[:]