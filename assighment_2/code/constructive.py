"""
Constructive heuristics for generating initial TSP tours
"""
import numpy as np


def nearest_neighbor(dist_matrix, start_city=0):
    """
    Construct a tour using nearest neighbor heuristic.
    
    Args:
        dist_matrix: n x n distance matrix
        start_city: starting city index
        
    Returns:
        tour: list of city indices
    """
    n = len(dist_matrix)
    unvisited = set(range(n))
    tour = [start_city]
    unvisited.remove(start_city)
    
    current = start_city
    while unvisited:
        # Find nearest unvisited city
        nearest = min(unvisited, key=lambda city: dist_matrix[current, city])
        tour.append(nearest)
        unvisited.remove(nearest)
        current = nearest
    
    return tour


def greedy_tour(dist_matrix):
    """
    Construct a tour by greedily adding the shortest edges that don't create a cycle
    or give a vertex degree > 2, until we have a complete tour.
    
    Args:
        dist_matrix: n x n distance matrix
        
    Returns:
        tour: list of city indices
    """
    n = len(dist_matrix)
    
    # Create list of all edges with their costs
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            edges.append((dist_matrix[i, j], i, j))
    
    # Sort edges by cost
    edges.sort()
    
    # Build tour using greedy approach
    degree = [0] * n
    adjacency = [[] for _ in range(n)]
    edge_count = 0
    
    for cost, i, j in edges:
        if edge_count == n:
            break
            
        # Check if we can add this edge
        if degree[i] < 2 and degree[j] < 2:
            # Check if it would create a premature cycle
            if edge_count < n - 1:
                # Don't create cycle unless it's the last edge
                if not would_create_cycle(adjacency, i, j, n):
                    adjacency[i].append(j)
                    adjacency[j].append(i)
                    degree[i] += 1
                    degree[j] += 1
                    edge_count += 1
            else:
                # Last edge, it should create the final cycle
                adjacency[i].append(j)
                adjacency[j].append(i)
                degree[i] += 1
                degree[j] += 1
                edge_count += 1
    
    # Convert adjacency list to tour
    tour = []
    current = 0
    prev = -1
    for _ in range(n):
        tour.append(current)
        # Find next city
        next_city = -1
        for neighbor in adjacency[current]:
            if neighbor != prev:
                next_city = neighbor
                break
        prev = current
        current = next_city
    
    return tour


def would_create_cycle(adjacency, u, v, n):
    """
    Check if adding edge (u, v) would create a cycle in the current graph.
    Uses BFS to check connectivity.
    """
    if not adjacency[u] or not adjacency[v]:
        return False
    
    # BFS from u to see if we can reach v
    visited = set([u])
    queue = [u]
    
    while queue:
        current = queue.pop(0)
        for neighbor in adjacency[current]:
            if neighbor == v:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return False


def savings_algorithm(dist_matrix):
    """
    Clarke-Wright savings algorithm for TSP.
    
    Args:
        dist_matrix: n x n distance matrix
        
    Returns:
        tour: list of city indices
    """
    n = len(dist_matrix)
    
    # Use depot as city 0
    depot = 0
    
    # Calculate savings for all pairs
    savings = []
    for i in range(1, n):
        for j in range(i + 1, n):
            s = dist_matrix[depot, i] + dist_matrix[depot, j] - dist_matrix[i, j]
            savings.append((s, i, j))
    
    # Sort by savings (descending)
    savings.sort(reverse=True)
    
    # Initialize routes (each city is its own route initially)
    routes = [[i] for i in range(1, n)]
    route_of = {i: i - 1 for i in range(1, n)}
    
    # Merge routes based on savings
    for s, i, j in savings:
        route_i = route_of.get(i, -1)
        route_j = route_of.get(j, -1)
        
        if route_i == -1 or route_j == -1 or route_i == route_j:
            continue
        
        # Check if i and j are at the ends of their routes
        route_i_list = routes[route_i]
        route_j_list = routes[route_j]
        
        if i == route_i_list[0] and j == route_j_list[-1]:
            # Merge j's route before i's route
            new_route = route_j_list + route_i_list
            routes[route_i] = new_route
            routes[route_j] = []
            for city in new_route:
                route_of[city] = route_i
        elif i == route_i_list[-1] and j == route_j_list[0]:
            # Merge j's route after i's route
            new_route = route_i_list + route_j_list
            routes[route_i] = new_route
            routes[route_j] = []
            for city in new_route:
                route_of[city] = route_i
        elif j == route_j_list[0] and i == route_i_list[-1]:
            # Merge i's route before j's route
            new_route = route_i_list + route_j_list
            routes[route_i] = new_route
            routes[route_j] = []
            for city in new_route:
                route_of[city] = route_i
        elif j == route_j_list[-1] and i == route_i_list[0]:
            # Merge i's route after j's route
            new_route = route_j_list + route_i_list
            routes[route_j] = new_route
            routes[route_i] = []
            for city in new_route:
                route_of[city] = route_j
    
    # Combine all routes into a single tour
    final_route = []
    for route in routes:
        if route:
            final_route.extend(route)
    
    # Add depot at the beginning
    tour = [depot] + final_route
    
    return tour


def best_nearest_neighbor(dist_matrix):
    """
    Try nearest neighbor from multiple starting cities and return the best tour.
    
    Args:
        dist_matrix: n x n distance matrix
        
    Returns:
        tour: list of city indices
    """
    n = len(dist_matrix)
    best_tour = None
    best_cost = float('inf')
    
    # Try different starting cities
    sample_size = min(n, 10)
    starts = np.random.choice(n, sample_size, replace=False)
    
    for start in starts:
        tour = nearest_neighbor(dist_matrix, start)
        cost = compute_tour_cost(tour, dist_matrix)
        if cost < best_cost:
            best_cost = cost
            best_tour = tour
    
    return best_tour


def compute_tour_cost(tour, dist_matrix):
    """Helper function to compute tour cost."""
    cost = 0.0
    for i in range(len(tour)):
        cost += dist_matrix[tour[i], tour[(i + 1) % len(tour)]]
    return cost
