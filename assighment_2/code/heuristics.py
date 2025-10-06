import time

import numpy as np

from utils import compute_cost, write_tour


def run_ga_lin_kernighan(
	dist_matrix: np.ndarray,
	time_limit: float | None = None,
	seed: int | None = None,
	neighbor_size: int | None = None,
	output_file: str | None = None,
	workers: int | None = None,
) -> tuple[list[int], list[list[int]]]:
	"""Solve TSP using a fast NN → 2-opt → Lin-Kernighan hybrid with restarts."""

	dist_matrix = np.asarray(dist_matrix, dtype=np.float64, order="C")
	n = dist_matrix.shape[0]
	if n <= 1:
		trivial = list(range(n))
		return trivial, [trivial]

	rng = np.random.default_rng(seed)
	time_limit = None if time_limit is None else max(0.0, float(time_limit))
	deadline = None if time_limit is None else time.time() + time_limit

	neighbor_size = neighbor_size or min(32, n - 1)
	neighbor_size = max(5, min(neighbor_size, n - 1))
	neighbor_lists = _build_neighbor_lists(dist_matrix, neighbor_size)
	positions = np.empty(n, dtype=np.int32)
	_ = workers  # retained for API compatibility with previous interface

	progress: list[list[int]] = []
	best_tour: list[int] | None = None
	best_cost = float("inf")

	def maybe_record(tour: list[int], cost: float) -> None:
		nonlocal best_tour, best_cost
		if cost + 1e-9 < best_cost:
			best_cost = cost
			best_tour = tour[:]
			progress.append(best_tour[:])
			if output_file is not None:
				try:
					write_tour(output_file, best_tour)
				except Exception:
					pass

	def run_pipeline(seed_tour: list[int]) -> tuple[list[int], float]:
		current, current_cost = _two_opt_hill_climb(
			seed_tour,
			dist_matrix,
			neighbor_lists,
			positions,
			deadline,
		)

		while True:
			if deadline is not None and time.time() >= deadline:
				break
			lk_tour, lk_cost = _lin_kernighan(
				current,
				dist_matrix,
				neighbor_lists,
				rng,
				deadline,
				positions,
				lk_max_no_improve=max(5, n // 40),
			)
			if lk_cost + 1e-9 < current_cost:
				current = lk_tour
				current_cost = lk_cost
				continue
			break

		return current, float(current_cost)

	initial_seed = _nearest_neighbor(dist_matrix, 0)
	initial_tour, initial_cost = run_pipeline(initial_seed)
	maybe_record(initial_tour, initial_cost)
	restarts = 1
	last_candidate: tuple[list[int], float] | None = (initial_tour, initial_cost)

	try:
		while True:
			if deadline is not None and time.time() >= deadline:
				break

			start_city = int(rng.integers(0, n))
			seed = _nearest_neighbor(dist_matrix, start_city)
			if rng.random() < 0.35 and n >= 12:
				seed = _double_bridge_move(seed, rng)

			candidate_tour, candidate_cost = run_pipeline(seed)
			last_candidate = (candidate_tour, candidate_cost)
			maybe_record(candidate_tour, candidate_cost)
			restarts += 1

			if deadline is None:
				# Allow gentle pacing when running indefinitely
				time.sleep(0.01)
	except KeyboardInterrupt:
		pass

	if best_tour is None and last_candidate is not None:
		best_tour, best_cost = last_candidate[0][:], float(last_candidate[1])
		progress.append(best_tour[:])

	if progress and best_tour is not None and progress[-1] != best_tour:
		progress.append(best_tour[:])

	return best_tour if best_tour is not None else list(range(n)), progress


# ---------------------------------------------------------------------------
# Search routines
# ---------------------------------------------------------------------------


def _two_opt_hill_climb(
	tour: list[int],
	dist_matrix: np.ndarray,
	neighbor_lists: np.ndarray,
	positions: np.ndarray,
	deadline: float | None,
) -> tuple[list[int], float]:
	current = tour[:]
	current_cost = compute_cost(current, dist_matrix)

	while True:
		if deadline is not None and time.time() >= deadline:
			break

		improved, delta, improved_tour = _best_improving_2opt_move(
			current,
			dist_matrix,
			neighbor_lists,
			positions,
		)

		if not improved:
			break

		current = improved_tour
		current_cost += delta

	return current, float(current_cost)


def _lin_kernighan(
	tour: list[int],
	dist_matrix: np.ndarray,
	neighbor_lists: np.ndarray,
	rng: np.random.Generator,
	deadline: float | None,
	positions: np.ndarray,
	lk_max_no_improve: int,
) -> tuple[list[int], float]:
	current = tour[:]
	current_cost = compute_cost(current, dist_matrix)
	best = current[:]
	best_cost = current_cost
	stagnation = 0

	while True:
		if deadline is not None and time.time() >= deadline:
			break

		improved, delta, improved_tour = _best_improving_2opt_move(
			current,
			dist_matrix,
			neighbor_lists,
			positions,
		)

		if improved:
			current = improved_tour
			current_cost += delta
			if current_cost + 1e-9 < best_cost:
				best = current[:]
				best_cost = current_cost
				stagnation = 0
			else:
				stagnation += 1
			continue

		stagnation += 1
		if stagnation >= lk_max_no_improve:
			break

		if rng.random() < 0.85:
			kicked = _double_bridge_move(best, rng)
		else:
			kicked = rng.permutation(current).tolist()
		current = kicked
		current_cost = compute_cost(current, dist_matrix)

	return best, float(best_cost)


def _best_improving_2opt_move(
	tour: list[int],
	dist_matrix: np.ndarray,
	neighbor_lists: np.ndarray,
	positions: np.ndarray,
) -> tuple[bool, float, list[int]]:
	n = len(tour)
	dm = dist_matrix
	_fill_positions(tour, positions)

	best_delta = 0.0
	best_pair: tuple[int, int] | None = None

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

			if (i - j) % n <= 1 or (j - i) % n <= 1:
				continue

			delta = dm[a, c] + dm[b, d] - dm[a, b] - dm[c, d]
			if delta < best_delta - 1e-12:
				best_delta = delta
				best_pair = (i, j)

	if best_pair is None:
		return False, 0.0, tour

	i, j = best_pair
	improved_tour = _apply_2opt(tour, i, j)
	return True, float(best_delta), improved_tour


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _build_neighbor_lists(dist_matrix: np.ndarray, neighbor_size: int) -> np.ndarray:
	n = dist_matrix.shape[0]
	if neighbor_size >= n - 1:
		order = np.argsort(dist_matrix, axis=1)
		return order[:, 1:]

	# Use argpartition for efficiency, then sort the selected neighbors.
	partition = np.argpartition(dist_matrix, range(1, neighbor_size + 1), axis=1)[:, 1 : neighbor_size + 1]
	neighbors = np.take_along_axis(dist_matrix, partition, axis=1)
	order = np.argsort(neighbors, axis=1)
	return np.take_along_axis(partition, order, axis=1).astype(np.int32)


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


def _fill_positions(tour: list[int], positions: np.ndarray) -> None:
	for idx, city in enumerate(tour):
		positions[city] = idx


def _apply_2opt(tour: list[int], i: int, j: int) -> list[int]:
	n = len(tour)
	if i == j:
		return tour[:]

	idxs: list[int] = []
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
	while attempts < 8:
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

