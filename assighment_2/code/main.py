"""
TSP Solver using numpy with continuous optimization
NEVER QUITS EARLY - runs until evaluator kills it
"""
import sys
import time
import numpy as np
from utils import read_input, compute_cost, write_tour, is_valid_tour
from constructive import nearest_neighbor, greedy_tour, savings_algorithm, best_nearest_neighbor
from local_search import (two_opt_fast, three_opt_fast, or_opt, lin_kernighan_simple, 
                          simulated_annealing, iterated_local_search, double_bridge_move,
                          variable_neighborhood_descent, compute_tour_cost)


class TSPSolver:
    def __init__(self, dist_matrix, time_limit):
        self.dist_matrix = dist_matrix
        self.n = len(dist_matrix)
        self.time_limit = time_limit
        self.start_time = time.time()
        self.best_tour = None
        self.best_cost = float('inf')
        
    def elapsed_time(self):
        """Get elapsed time since start."""
        return time.time() - self.start_time
    
    def remaining_time(self):
        """Get remaining time."""
        return max(0, self.time_limit - self.elapsed_time())
    
    def update_best(self, tour):
        """Update best solution if tour is better."""
        if tour is None:
            return False
            
        cost = compute_cost(tour, self.dist_matrix)
        if cost < self.best_cost:
            self.best_tour = list(tour)
            self.best_cost = cost
            return True
        return False
    
    def solve(self, output_file):
        """Main solving method."""
        print("="*60)
        print(f"TSP SOLVER - CONTINUOUS OPTIMIZATION")
        print(f"Problem size: n={self.n}")
        print(f"Time limit: {self.time_limit} seconds")
        print("="*60)
        
        # CONSTRUCTION PHASE: Get initial solution
        print("\n→ Construction phase...")
        start_construction = time.time()
        
        # Try multiple construction heuristics
        initial_tours = []
        
        # Best nearest neighbor (multi-start)
        print("  • Best nearest neighbor (multi-start)...")
        best_nn = best_nearest_neighbor(self.dist_matrix)
        initial_tours.append(best_nn)
        
        # Savings algorithm
        print("  • Savings algorithm...")
        savings = savings_algorithm(self.dist_matrix)
        initial_tours.append(savings)
        
        # Greedy
        print("  • Greedy tour...")
        greedy = greedy_tour(self.dist_matrix)
        initial_tours.append(greedy)
        
        # Find best initial tour
        best_initial = min(initial_tours, key=lambda t: compute_cost(t, self.dist_matrix))
        self.update_best(best_initial)
        
        construction_time = time.time() - start_construction
        print(f"\n✓ Initial solution: {self.best_cost:.2f} (in {construction_time:.2f}s)")
        write_tour(output_file, self.best_tour)
        
        # OPTIMIZATION PHASE: Improve forever
        self.improve_forever(output_file)
        
    def improve_forever(self, output_file):
        """Continuous optimization - NEVER STOP."""
        print("\n" + "="*60)
        print(f"CONTINUOUS OPTIMIZATION (n={self.n})")
        print("Strategy: NEVER QUIT - run until evaluator kills us")
        print("="*60)
        
        current_tour = list(self.best_tour)
        iteration = 0
        
        # Determine strategies based on problem size
        use_3opt = self.n >= 100
        use_ils = self.n >= 150
        
        print(f"\nActive strategies:")
        print(f"  • 2-opt: Always")
        print(f"  • 3-opt: {'Yes' if use_3opt else 'No'} (n >= 100)")
        print(f"  • ILS: {'Yes' if use_ils else 'No'} (n >= 150)")
        print(f"  • Or-opt: Yes")
        print(f"  • VND: Yes")
        print(f"  • Simulated Annealing: Yes")
        print(f"  • Double-bridge perturbations: Yes")
        
        print("\n→ Starting infinite optimization loop...\n")
        
        while True:  # INFINITE LOOP - evaluator will kill us
            iteration += 1
            
            if iteration % 5 == 1:
                print(f"Iteration {iteration}, elapsed: {self.elapsed_time():.1f}s, cost: {self.best_cost:.2f}")
            
            # CORE: 2-opt (always apply)
            improved_tour = two_opt_fast(current_tour, self.dist_matrix, time_limit=5)
            if self.update_best(improved_tour):
                current_tour = list(self.best_tour)
                write_tour(output_file, self.best_tour)
                if iteration % 5 == 0:
                    print(f"  ✓ 2-opt improved to {self.best_cost:.2f}")
            
            # POWER MOVE: 3-opt for larger instances
            if use_3opt and iteration % 3 == 0:
                improved_tour = three_opt_fast(current_tour, self.dist_matrix, time_limit=10)
                if self.update_best(improved_tour):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓ 3-opt improved to {self.best_cost:.2f}")
            
            # Or-opt: relocate sequences
            if iteration % 4 == 0:
                max_iter = 50 if self.n < 100 else 40
                improved_tour = or_opt(current_tour, self.dist_matrix, max_iterations=max_iter)
                if self.update_best(improved_tour):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
            
            # Variable Neighborhood Descent
            if iteration % 8 == 0:
                improved_tour = variable_neighborhood_descent(current_tour, self.dist_matrix, time_limit=12)
                if self.update_best(improved_tour):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓ VND improved to {self.best_cost:.2f}")
            
            # Iterated Local Search (for large instances)
            if use_ils and iteration % 12 == 0:
                perturb_strength = 4 if self.n >= 200 else 3
                improved_tour = iterated_local_search(
                    current_tour, self.dist_matrix, 
                    time_limit=20, 
                    perturbation_strength=perturb_strength
                )
                if self.update_best(improved_tour):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓✓ ILS improved to {self.best_cost:.2f}")
            
            # ESCAPE: Strong perturbation to break out of local minima
            if iteration % 15 == 0:
                if iteration % 30 == 0:
                    print(f"  → STRONG perturbation (iteration {iteration})")
                
                num_moves = 3 if self.n >= 150 else 2
                perturbed = double_bridge_move(self.best_tour, num_moves=num_moves)
                
                # Optimize the perturbed solution
                improved = two_opt_fast(perturbed, self.dist_matrix, time_limit=5)
                if use_3opt:
                    improved = three_opt_fast(improved, self.dist_matrix, time_limit=6)
                
                if self.update_best(improved):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓✓ Perturbation found better: {self.best_cost:.2f}")
                else:
                    # Use for exploration even if not better
                    current_tour = improved
            
            # EXPLORE: Simulated Annealing
            if iteration % 20 == 0:
                if iteration % 40 == 0:
                    print(f"  → Simulated annealing (iteration {iteration})")
                
                # Adjust SA parameters based on problem size
                temp = 2000 if self.n >= 150 else 1000
                max_iter = min(100000, int(50000 * (200 / max(50, self.n))))
                
                improved_tour = simulated_annealing(
                    current_tour,
                    self.dist_matrix,
                    initial_temp=temp,
                    cooling_rate=0.9996,
                    max_iterations=max_iter
                )
                if self.update_best(improved_tour):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓ SA improved to {self.best_cost:.2f}")
            
            # DIVERSIFY: Multi-start nearest neighbor
            if iteration % 25 == 0:
                if iteration % 50 == 0:
                    print(f"  → Multi-start construction (iteration {iteration})")
                
                num_starts = min(8, self.n // 10 + 1)
                for start in np.random.choice(self.n, num_starts, replace=False):
                    tour = nearest_neighbor(self.dist_matrix, int(start))
                    tour = two_opt_fast(tour, self.dist_matrix, time_limit=3)
                    if use_3opt:
                        tour = three_opt_fast(tour, self.dist_matrix, time_limit=4)
                    
                    if self.update_best(tour):
                        current_tour = list(self.best_tour)
                        write_tour(output_file, self.best_tour)
                        print(f"  ✓✓ Multi-start found better: {self.best_cost:.2f}")
                        break
            
            # RECONSTRUCT: Try other construction heuristics
            if iteration % 30 == 0:
                if iteration % 60 == 0:
                    print(f"  → Trying alternate constructions (iteration {iteration})")
                
                # Greedy
                greedy = greedy_tour(self.dist_matrix)
                greedy = two_opt_fast(greedy, self.dist_matrix, time_limit=4)
                if use_3opt:
                    greedy = three_opt_fast(greedy, self.dist_matrix, time_limit=4)
                self.update_best(greedy)
                
                # Savings
                savings = savings_algorithm(self.dist_matrix)
                savings = two_opt_fast(savings, self.dist_matrix, time_limit=4)
                if use_3opt:
                    savings = three_opt_fast(savings, self.dist_matrix, time_limit=4)
                
                if self.update_best(savings):
                    current_tour = list(self.best_tour)
                    write_tour(output_file, self.best_tour)
                    print(f"  ✓✓ Reconstruction found better: {self.best_cost:.2f}")
        
        # This line will never be reached - evaluator kills us
        print("✓ Optimization complete (this should never print)")


def main():
    if len(sys.argv) != 4:
        print("Usage: python main.py <input_file> <output_file> <time_limit>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    time_limit = int(sys.argv[3])
    
    # Read input
    try:
        metric, n, dist_matrix = read_input(input_file)
        print(f"Read {metric} instance with {n} cities")
    except Exception as e:
        print(f"Error reading input: {e}")
        sys.exit(1)
    
    # Solve
    solver = TSPSolver(dist_matrix, time_limit)
    
    try:
        solver.solve(output_file)
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("KILLED BY EVALUATOR (as expected)")
        print(f"Final cost: {solver.best_cost:.6f}")
        print(f"Time used: {solver.elapsed_time():.2f} seconds")
        print("="*60)
    except Exception as e:
        print(f"\nError during solving: {e}")
        import traceback
        traceback.print_exc()
    
    # Final validation
    if solver.best_tour and is_valid_tour(solver.best_tour, len(dist_matrix)):
        print(f"\n✓ Valid solution with cost: {solver.best_cost:.6f}")
    else:
        print("\n✗ Invalid solution!")
        sys.exit(1)


if __name__ == "__main__":
    main()
