"""
Local search improvement heuristics for TSP
"""
import numpy as np


def two_opt(tour, dist_matrix, max_iterations=None):
    """
    Improve tour using 2-opt local search.
    
    Args:
        tour: initial tour (list of city indices)
        dist_matrix: n x n distance matrix
        max_iterations: maximum number of iterations (None for unlimited)
        
    Returns:
        improved_tour: optimized tour
        improved: whether any improvement was made
    """
    tour = list(tour)
    n = len(tour)
    improved = True
    iterations = 0
    
    while improved:
        improved = False
        if max_iterations and iterations >= max_iterations:
            break
        iterations += 1
        
        for i in range(n - 1):
            for j in range(i + 2, n):
                # Calculate the change in cost if we reverse tour[i+1:j+1]
                # Current edges: (tour[i], tour[i+1]) and (tour[j], tour[j+1])
                # New edges: (tour[i], tour[j]) and (tour[i+1], tour[j+1])
                
                i_next = (i + 1) % n
                j_next = (j + 1) % n
                
                current_cost = (dist_matrix[tour[i], tour[i_next]] + 
                               dist_matrix[tour[j], tour[j_next]])
                new_cost = (dist_matrix[tour[i], tour[j]] + 
                           dist_matrix[tour[i_next], tour[j_next]])
                
                if new_cost < current_cost:
                    # Reverse the segment
                    tour[i + 1:j + 1] = reversed(tour[i + 1:j + 1])
                    improved = True
    
    return tour, iterations > 1


def two_opt_fast(tour, dist_matrix, time_limit=None):
    """
    Fast 2-opt with early termination and optimizations.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        time_limit: time limit in seconds
        
    Returns:
        improved tour
    """
    import time
    start_time = time.time() if time_limit else None
    
    tour = np.array(tour, dtype=np.int32)
    n = len(tour)
    improved = True
    
    while improved:
        if time_limit and (time.time() - start_time) > time_limit:
            break
            
        improved = False
        for i in range(n - 1):
            if time_limit and (time.time() - start_time) > time_limit:
                break
                
            for j in range(i + 2, n):
                # Avoid checking last edge wrapping
                if j == n - 1 and i == 0:
                    continue
                
                i_next = i + 1
                j_next = (j + 1) % n
                
                delta = (dist_matrix[tour[i], tour[j]] + 
                        dist_matrix[tour[i_next], tour[j_next]] -
                        dist_matrix[tour[i], tour[i_next]] - 
                        dist_matrix[tour[j], tour[j_next]])
                
                if delta < -1e-9:  # Small epsilon for numerical stability
                    # Reverse segment
                    tour[i_next:j + 1] = tour[i_next:j + 1][::-1]
                    improved = True
    
    return tour.tolist()


def three_opt_fast(tour, dist_matrix, time_limit=None):
    """
    Fast 3-opt implementation with time limit.
    Much more powerful than 2-opt for escaping local minima.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        time_limit: time limit in seconds
        
    Returns:
        improved tour
    """
    import time
    start_time = time.time() if time_limit else None
    
    tour = np.array(tour, dtype=np.int32)
    n = len(tour)
    improved = True
    
    while improved:
        if time_limit and (time.time() - start_time) > time_limit:
            break
            
        improved = False
        
        for i in range(n):
            if time_limit and (time.time() - start_time) > time_limit:
                break
                
            for j in range(i + 2, n):
                if time_limit and (time.time() - start_time) > time_limit:
                    break
                    
                for k in range(j + 2, n + (1 if i > 0 else 0)):
                    # Get the three edges to remove
                    A, B = tour[i], tour[(i + 1) % n]
                    C, D = tour[j], tour[(j + 1) % n]
                    E, F = tour[k % n], tour[(k + 1) % n]
                    
                    # Current cost
                    d0 = dist_matrix[A, B] + dist_matrix[C, D] + dist_matrix[E, F]
                    
                    # Try all 4 non-trivial reconnections (there are 7 total, 3 are equivalent to 2-opt)
                    
                    # Case 1: A-C, B-E, D-F (reverse middle segment)
                    d1 = dist_matrix[A, C] + dist_matrix[B, E] + dist_matrix[D, F]
                    if d1 < d0 - 1e-9:
                        # Reconnect: reverse segment (i+1) to j
                        new_tour = np.concatenate([
                            tour[:i+1],
                            tour[i+1:j+1][::-1],
                            tour[j+1:]
                        ])
                        tour = new_tour
                        improved = True
                        break
                    
                    # Case 2: A-D, C-E, B-F (reverse last segment and swap middle-last)
                    d2 = dist_matrix[A, D] + dist_matrix[C, E] + dist_matrix[B, F]
                    if d2 < d0 - 1e-9:
                        # Reconnect
                        new_tour = np.concatenate([
                            tour[:i+1],
                            tour[j+1:k+1],
                            tour[i+1:j+1],
                            tour[k+1:]
                        ])
                        tour = new_tour
                        improved = True
                        break
                    
                    # Case 3: A-E, D-B, C-F (reverse and reorder)
                    d3 = dist_matrix[A, E] + dist_matrix[D, B] + dist_matrix[C, F]
                    if d3 < d0 - 1e-9:
                        new_tour = np.concatenate([
                            tour[:i+1],
                            tour[j+1:k+1][::-1],
                            tour[i+1:j+1],
                            tour[k+1:]
                        ])
                        tour = new_tour
                        improved = True
                        break
                    
                    # Case 4: A-D, C-B, E-F (reverse first two segments and swap)
                    d4 = dist_matrix[A, D] + dist_matrix[C, B] + dist_matrix[E, F]
                    if d4 < d0 - 1e-9:
                        new_tour = np.concatenate([
                            tour[:i+1],
                            tour[j+1:k+1],
                            tour[i+1:j+1][::-1],
                            tour[k+1:]
                        ])
                        tour = new_tour
                        improved = True
                        break
                
                if improved:
                    break
            if improved:
                break
    
    return tour.tolist()


def generate_3opt_neighbors(tour, i, j, k):
    """Generate possible 3-opt reconnections."""
    n = len(tour)
    neighbors = []
    
    # There are 8 ways to reconnect 3 edges, we try a few important ones
    # Reverse segment i+1 to j
    tour1 = tour[:i+1] + tour[i+1:j+1][::-1] + tour[j+1:]
    neighbors.append(tour1)
    
    # Reverse segment j+1 to k
    tour2 = tour[:j+1] + tour[j+1:k+1][::-1] + tour[k+1:]
    neighbors.append(tour2)
    
    # Swap segments
    tour3 = tour[:i+1] + tour[j+1:k+1] + tour[i+1:j+1] + tour[k+1:]
    neighbors.append(tour3)
    
    return neighbors


def compute_segment_cost(tour, dist_matrix, i, j, k):
    """Compute cost of edges around segments i, j, k."""
    n = len(tour)
    edges = [
        (tour[i], tour[i+1]),
        (tour[j], tour[j+1]),
        (tour[k], tour[(k+1) % n])
    ]
    cost = sum(dist_matrix[a, b] for a, b in edges)
    return cost


def or_opt(tour, dist_matrix, max_iterations=100):
    """
    Or-opt local search: relocate sequences of 1, 2, or 3 consecutive cities.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        max_iterations: maximum iterations
        
    Returns:
        improved tour
    """
    tour = list(tour)
    n = len(tour)
    
    for iteration in range(max_iterations):
        improved = False
        
        # Try relocating sequences of length 1, 2, and 3
        for seq_len in [1, 2, 3]:
            if improved:
                break
                
            for i in range(n):
                if improved:
                    break
                    
                for j in range(n):
                    if abs(i - j) <= seq_len:
                        continue
                    
                    # Try moving sequence starting at i to position after j
                    new_tour = relocate_sequence(tour, i, seq_len, j)
                    
                    if compute_tour_cost(new_tour, dist_matrix) < compute_tour_cost(tour, dist_matrix):
                        tour = new_tour
                        improved = True
                        break
        
        if not improved:
            break
    
    return tour


def relocate_sequence(tour, start, length, target):
    """Relocate a sequence of cities in the tour."""
    n = len(tour)
    tour = list(tour)
    
    # Extract sequence
    seq = []
    for i in range(length):
        seq.append(tour[(start + i) % n])
    
    # Remove sequence
    new_tour = []
    for i in range(n):
        if not (start <= i < start + length):
            new_tour.append(tour[i])
    
    # Insert at new position
    if target >= start:
        target -= length
    
    target = max(0, min(target, len(new_tour)))
    result = new_tour[:target + 1] + seq + new_tour[target + 1:]
    
    return result


def compute_tour_cost(tour, dist_matrix):
    """Compute total cost of a tour."""
    cost = 0.0
    for i in range(len(tour)):
        cost += dist_matrix[tour[i], tour[(i + 1) % len(tour)]]
    return cost


def lin_kernighan_simple(tour, dist_matrix, max_iterations=50):
    """
    Simplified Lin-Kernighan heuristic using sequential edge exchanges.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        max_iterations: maximum iterations
        
    Returns:
        improved tour
    """
    tour = np.array(tour, dtype=np.int32)
    n = len(tour)
    
    for iteration in range(max_iterations):
        improved = False
        
        # Try to find improving k-opt moves (k=2,3,4)
        for i in range(n):
            # Build candidate edges for exchange
            current_city = tour[i]
            next_city = tour[(i + 1) % n]
            
            # Find cities close to current_city that might improve the tour
            distances = dist_matrix[current_city]
            candidates = np.argsort(distances)[:10]  # Top 10 nearest
            
            for candidate in candidates:
                if candidate == current_city or candidate == next_city:
                    continue
                
                # Try swapping edge (current, next) with edge to candidate
                # This is a simplified version - full LK is more complex
                candidate_idx = np.where(tour == candidate)[0][0]
                
                # Try 2-opt style move
                if candidate_idx != (i + 1) % n and candidate_idx != i:
                    i_next = (i + 1) % n
                    c_next = (candidate_idx + 1) % n
                    
                    current_cost = (dist_matrix[tour[i], tour[i_next]] + 
                                  dist_matrix[tour[candidate_idx], tour[c_next]])
                    new_cost = (dist_matrix[tour[i], tour[candidate_idx]] + 
                              dist_matrix[tour[i_next], tour[c_next]])
                    
                    if new_cost < current_cost:
                        # Reverse segment
                        if i < candidate_idx:
                            tour[i + 1:candidate_idx + 1] = tour[i + 1:candidate_idx + 1][::-1]
                        else:
                            tour[candidate_idx + 1:i + 1] = tour[candidate_idx + 1:i + 1][::-1]
                        improved = True
                        break
            
            if improved:
                break
        
        if not improved:
            break
    
    return tour.tolist()


def simulated_annealing(tour, dist_matrix, initial_temp=1000, cooling_rate=0.995, max_iterations=10000):
    """
    Simulated annealing for TSP.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        initial_temp: starting temperature
        cooling_rate: cooling rate (< 1)
        max_iterations: maximum iterations
        
    Returns:
        best tour found
    """
    current_tour = list(tour)
    current_cost = compute_tour_cost(current_tour, dist_matrix)
    
    best_tour = list(current_tour)
    best_cost = current_cost
    
    temp = initial_temp
    n = len(tour)
    
    for iteration in range(max_iterations):
        # Generate neighbor by 2-opt move
        i = np.random.randint(0, n - 1)
        j = np.random.randint(i + 2, min(n + 1, i + n))
        j = j % n
        
        if i >= j or j - i < 2:
            continue
        
        # Reverse segment
        new_tour = current_tour[:i+1] + current_tour[i+1:j+1][::-1] + current_tour[j+1:]
        new_cost = compute_tour_cost(new_tour, dist_matrix)
        
        # Accept or reject
        delta = new_cost - current_cost
        if delta < 0 or np.random.random() < np.exp(-delta / temp):
            current_tour = new_tour
            current_cost = new_cost
            
            if current_cost < best_cost:
                best_tour = list(current_tour)
                best_cost = current_cost
        
        # Cool down
        temp *= cooling_rate
        
        if temp < 1e-8:
            break
    
    return best_tour


def iterated_local_search(tour, dist_matrix, time_limit=None, perturbation_strength=4):
    """
    Iterated Local Search: Apply local search, perturb, repeat.
    Very effective for escaping local minima.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        time_limit: time limit in seconds
        perturbation_strength: number of double-bridge moves
        
    Returns:
        best tour found
    """
    import time
    start_time = time.time() if time_limit else None
    
    current_tour = list(tour)
    current_cost = compute_tour_cost(current_tour, dist_matrix)
    
    best_tour = list(current_tour)
    best_cost = current_cost
    
    n = len(tour)
    iteration = 0
    
    while True:
        if time_limit and (time.time() - start_time) > time_limit:
            break
        
        iteration += 1
        
        # Local search phase
        time_remaining = time_limit - (time.time() - start_time) if time_limit else 5
        current_tour = two_opt_fast(current_tour, dist_matrix, time_limit=min(5, time_remaining))
        current_cost = compute_tour_cost(current_tour, dist_matrix)
        
        # Update best
        if current_cost < best_cost:
            best_tour = list(current_tour)
            best_cost = current_cost
        
        if time_limit and (time.time() - start_time) > time_limit:
            break
        
        # Perturbation phase: double-bridge move
        current_tour = double_bridge_move(current_tour, perturbation_strength)
        current_cost = compute_tour_cost(current_tour, dist_matrix)
    
    return best_tour


def double_bridge_move(tour, num_moves=1):
    """
    Apply double-bridge perturbation to escape local minima.
    This is a 4-opt move that cannot be undone by 2-opt or 3-opt.
    
    Args:
        tour: current tour
        num_moves: number of double-bridge moves to apply
        
    Returns:
        perturbed tour
    """
    tour = list(tour)
    n = len(tour)
    
    for _ in range(num_moves):
        # Choose 4 random positions
        positions = sorted(np.random.choice(n, 4, replace=False))
        i, j, k, l = positions
        
        # Apply double-bridge: A-B-C-D-A becomes A-D-C-B-A
        # Where A = [0:i], B = [i:j], C = [j:k], D = [k:l], E = [l:]
        tour = tour[:i] + tour[k:l] + tour[j:k] + tour[i:j] + tour[l:]
    
    return tour


def variable_neighborhood_descent(tour, dist_matrix, time_limit=None):
    """
    Variable Neighborhood Descent: systematically try different neighborhoods.
    
    Args:
        tour: initial tour
        dist_matrix: distance matrix
        time_limit: time limit in seconds
        
    Returns:
        improved tour
    """
    import time
    start_time = time.time() if time_limit else None
    
    current_tour = list(tour)
    n = len(tour)
    
    # Define neighborhoods in order of increasing complexity
    neighborhoods = [
        ('2-opt', lambda t: two_opt_fast(t, dist_matrix, time_limit=3)),
        ('or-opt', lambda t: or_opt(t, dist_matrix, max_iterations=20)),
        ('3-opt', lambda t: three_opt_fast(t, dist_matrix, time_limit=5)),
    ]
    
    k = 0  # Current neighborhood index
    
    while k < len(neighborhoods):
        if time_limit and (time.time() - start_time) > time_limit:
            break
        
        name, improve_func = neighborhoods[k]
        
        # Try to improve in current neighborhood
        improved_tour = improve_func(current_tour)
        improved_cost = compute_tour_cost(improved_tour, dist_matrix)
        current_cost = compute_tour_cost(current_tour, dist_matrix)
        
        if improved_cost < current_cost - 1e-9:
            # Found improvement, restart from first neighborhood
            current_tour = improved_tour
            k = 0
        else:
            # No improvement, try next neighborhood
            k += 1
    
    return current_tour
