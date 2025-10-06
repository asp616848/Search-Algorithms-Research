"""
Utility functions for TSP solver
"""
import numpy as np
from pathlib import Path


def read_input(filepath):
    """
    Read TSP input file and return metric type, number of cities, and distance matrix.
    
    Args:
        filepath: path to input file
        
    Returns:
        metric: 'EUCLIDEAN' or 'NON-EUCLIDEAN'
        n: number of cities
        dist_matrix: n x n numpy array of distances
    """
    # Try different encodings
    for encoding in ['utf-16', 'utf-16-le', 'utf-8', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                lines = [line.strip() for line in f if line.strip()]
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        raise ValueError(f"Could not decode file {filepath} with any known encoding")
    
    metric = lines[0]
    n = int(lines[1])
    
    dist_matrix = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        values = list(map(float, lines[2 + i].split()))
        dist_matrix[i, :] = values
    
    return metric, n, dist_matrix


def compute_cost(tour, dist_matrix):
    """
    Compute the total cost of a tour.
    
    Args:
        tour: list or array of city indices representing the tour
        dist_matrix: distance matrix
        
    Returns:
        total cost of the tour
    """
    if len(tour) == 0:
        return 0.0
    
    tour = np.asarray(tour, dtype=int)
    cost = 0.0
    for i in range(len(tour)):
        cost += dist_matrix[tour[i], tour[(i + 1) % len(tour)]]
    return cost


def write_tour(filepath, tour):
    """
    Append a tour to the output file.
    
    Args:
        filepath: output file path
        tour: list or array of city indices
    """
    with open(filepath, 'a') as f:
        f.write(' '.join(map(str, tour)) + '\n')


def is_valid_tour(tour, n):
    """
    Check if a tour is valid (contains all cities exactly once).
    
    Args:
        tour: list or array of city indices
        n: number of cities
        
    Returns:
        True if valid, False otherwise
    """
    if len(tour) != n:
        return False
    return len(set(tour)) == n and all(0 <= i < n for i in tour)
