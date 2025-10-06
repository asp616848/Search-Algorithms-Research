# TSP Solver - Assignment 2

A comprehensive Traveling Salesman Problem (TSP) solver using only NumPy, implementing multiple heuristics for finding near-optimal solutions.

## Files

- **main.py**: Main orchestrator that manages time and coordinates different optimization strategies
- **utils.py**: Utility functions for reading input, computing costs, and writing output
- **constructive.py**: Constructive heuristics for generating initial solutions (Nearest Neighbor, Greedy, Savings Algorithm)
- **local_search.py**: Local search improvement methods (2-opt, 3-opt, Or-opt, Lin-Kernighan, Simulated Annealing)
- **runner.py**: Test runner for evaluating performance across all test cases

## Algorithm Strategy

### Phase 1: Initial Solution Construction (10-15% of time)
1. **Multi-start Nearest Neighbor**: Generate solutions from multiple starting cities
2. **Greedy Construction**: Build tour by adding shortest edges
3. **Savings Algorithm**: Clarke-Wright savings heuristic  
4. **Quick 2-opt**: Apply fast 2-opt to each initial solution

### Phase 2: Intensive Local Search (80-85% of time)
Iteratively applies multiple improvement heuristics:
1. **2-opt optimization**: Fast edge-swapping local search (most time-intensive)
2. **Or-opt**: Relocate sequences of 1-3 cities
3. **Lin-Kernighan**: Simplified variable-depth search
4. **Simulated Annealing**: Probabilistic exploration (early iterations only)
5. **Perturbation**: Random modifications to escape local optima

### Phase 3: Final Polish (remaining time)
- Final 2-opt pass to squeeze out last improvements

## Key Features

- **Progressive Output**: Continuously writes improved solutions to output file
- **Time Management**: Intelligent allocation of remaining time across strategies
- **UTF-16 Support**: Handles both UTF-8 and UTF-16 encoded input files
- **Early Termination**: Stops gracefully when no improvement for 20 iterations
- **Adaptive Strategy**: Adjusts iteration counts based on remaining time

## Usage

```bash
python3 main.py <input_file> <output_file> <time_limit_seconds>
```

Example:
```bash
python3 main.py ../EUCLIDEAN_50.txt output.txt 300
```

## Running All Tests

```bash
export RUN_TIMEOUT=300  # 300 seconds per test
python3 runner.py
```

This will test all 6 problem instances and create a summary in `summary_output.txt`.

## Dependencies

- Python 3.x
- NumPy

## Implementation Details

### 2-opt Optimization
The core optimization loop uses efficient 2-opt with:
- Early termination based on time limit
- Small epsilon (1e-9) for numerical stability
- In-place array modifications for speed

### Tour Representation
Tours are represented as lists of city indices (0 to N-1), forming a cycle where the last city connects back to the first.

### Cost Calculation
Tour cost is the sum of Euclidean/Non-Euclidean distances between consecutive cities in the tour, including the edge from the last city back to the first.

## Expected Performance

For 300-second timeout:
- **50-city instances**: Solutions within 5-10% of optimal
- **100-city instances**: Solutions within 10-15% of optimal
- **200-city instances**: Solutions within 15-25% of optimal

Results vary based on problem structure (Euclidean vs Non-Euclidean).

## Author

Created for AI3002 - Search Methods in AI
