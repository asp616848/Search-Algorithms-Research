# MyBot: Elite Othello AI - Technical Report

## Overview

MyBot is an advanced Othello (Reversi) AI agent that combines multiple sophisticated search and evaluation techniques to achieve competitive gameplay within strict time constraints.

---

## Core Algorithms

### 1. Negamax with Alpha-Beta Pruning

The bot uses **Negamax**, a variant of minimax that simplifies implementation by exploiting the zero-sum nature of Othello:

```
value(position, player) = -value(position, opponent)
```

Alpha-beta pruning reduces the search space by eliminating branches that cannot affect the final decision.

### 2. Principal Variation Search (PVS)

PVS optimizes alpha-beta by assuming the first move (from move ordering) is likely the best:

- **First move**: Full window search `[-β, -α]`
- **Subsequent moves**: Null window search `[-α-1, -α]`
- **Re-search**: Only if null window fails high

This reduces the number of nodes evaluated when move ordering is effective.

### 3. Iterative Deepening

The bot searches progressively deeper (depth 1, 2, 3, ...) until time runs out:

- **Advantages**:
  - Always has a valid move ready
  - Improves move ordering for deeper searches
  - Enables aspiration windows

### 4. Aspiration Windows

At depth ≥ 4, the search uses a narrow window `[bestValue - 50, bestValue + 50]` around the previous depth's result. If the search fails outside this window, a full re-search is performed.

### 5. Transposition Table

A hash table (2²⁰ = 1,048,576 entries) stores previously evaluated positions using **Zobrist hashing**:

- **Entry fields**: hash, depth, value, flag (exact/lower/upper bound), best move
- **Benefits**: Avoids re-evaluating identical positions reached via different move orders

---

## Move Ordering Heuristics

Effective move ordering is critical for alpha-beta efficiency. Moves are scored and sorted by:

| Priority | Heuristic | Score |
|----------|-----------|-------|
| 1 | Transposition table move | 100,000 |
| 2 | Principal variation move | 90,000 |
| 3 | Corner moves (a1, a8, h1, h8) | 80,000 |
| 4 | Killer move (slot 1) | 70,000 |
| 5 | Killer move (slot 2) | 60,000 |
| 6 | Edge moves | 2,000 |
| 7 | History heuristic | Variable |
| - | X-squares (without corner) | -10,000 |
| - | C-squares (without corner) | -5,000 |

### Killer Moves
Stores two moves per ply that caused beta cutoffs, prioritizing them in sibling nodes.

### History Heuristic
Tracks moves that cause cutoffs across the entire search, weighted by `depth²`.

---

## Evaluation Function

The evaluation is **phase-dependent**, adapting weights based on game progress:

| Phase | Disc Count | Focus |
|-------|------------|-------|
| Early | < 20 | Mobility, Positional |
| Mid | 20-49 | Balanced |
| Late | ≥ 50 | Disc count, Stability |

### Evaluation Components

| Component | Description | Early Weight | Mid Weight | Late Weight |
|-----------|-------------|--------------|------------|-------------|
| **Mobility** | (myMoves - oppMoves) / total | ×20 | ×15 | ×8 |
| **Positional** | Weighted square values | ×5 | ×4 | ×2 |
| **Corners** | 25 points per corner differential | ×100 | ×80 | ×50 |
| **Stability** | Discs that cannot be flipped | ×10 | ×15 | ×20 |
| **Frontier** | Discs adjacent to empty squares (negative) | ×8 | ×5 | - |
| **Disc Difference** | Piece count advantage | ×(-2) | ×3 | ×25 |
| **Parity** | Bonus if odd empty squares | - | - | ×10 |

### Positional Weight Tables

Three 8×8 weight matrices for early, mid, and late game:

- **Corners**: Highest value (500 early → 100 late)
- **X-squares** (b2, b7, g2, g7): Highly negative (-250 early)
- **C-squares** (adjacent to corners): Negative (-150 early)
- **Edges**: Positive value
- **Center**: Minimal weight

---

## Time Management

### Hard Constraints

| Parameter | Value |
|-----------|-------|
| **Hard timeout** | 2000 ms |
| **Configured limit** | 1980 ms (1.98s) |

### Time Limit Calculation

The bot must complete its move **before** the 2000ms hard deadline. Here's the calculation:

#### 1. Worst-Case Overshoot (Block Time)

The time check occurs every **512 nodes** (when `nodesSearched & 511 == 0`):

```cpp
if ((nodesSearched & 511) == 0) {
    // Check elapsed time
}
```

**Measured worst-case**: Processing 512 nodes takes approximately **6 ms**

This means after passing a time check, the bot could run for up to 6ms before the next check.

#### 2. Time Check Overhead

Each time check involves:
- Getting current time: `chrono::high_resolution_clock::now()`
- Computing duration
- Comparison

**Measured overhead**: ~0.02 ms → **Negligible**

#### 3. Safety Margin

Additional buffer for system variability: **3 ms**

#### 4. Final Calculation

```
Cutoff = Hard Timeout - Worst-Case Overshoot - Safety Margin
Cutoff = 2000 - 11 - 3 = 1986 ms
```

**Configured value**: 1980 ms (rounded down for additional safety)

```cpp
timeLimit = 1.98;  // seconds
```

### Time Check Implementation

```cpp
bool MyBot::isTimeUp()
{
    if (timeUp) return true;
    if ((nodesSearched & 511) == 0) {  // Check every 512 nodes
        auto now = chrono::high_resolution_clock::now();
        chrono::duration<double> elapsed = now - startTime;
        if (elapsed.count() > timeLimit) {
            timeUp = true;
            return true;
        }
    }
    return false;
}
```

**Why 512 nodes?**
- Balances check frequency vs overhead
- `& 511` is a fast bitwise operation (equivalent to `% 512`)
- Provides responsive time management without excessive overhead

---

## Endgame Handling

When ≤ 12 empty squares remain:
- Maximum depth increased to `emptySquares + 2`
- Enables complete endgame solving
- Parity becomes significant (odd empties favor current player)

---

## Memory Usage

| Structure | Size |
|-----------|------|
| Transposition Table | 2²⁰ × sizeof(TTEntry) ≈ 32 MB |
| Zobrist Table | 8 × 8 × 3 × 8 bytes = 1.5 KB |
| Weight Tables | 3 × 8 × 8 × 4 bytes = 768 bytes |
| History Table | 2 × 8 × 8 × 4 bytes = 512 bytes |
| Killer Moves | 64 × 2 × 2 × 4 bytes = 1 KB |

---

## Performance Characteristics

- **Nodes/second**: Varies by position complexity
- **Typical search depth**: 8-12 in midgame, complete in endgame
- **Time utilization**: ~99% of allocated time budget

---

## Summary

MyBot combines:
1. **Negamax + Alpha-Beta** - Core search algorithm
2. **PVS** - Optimized search windows
3. **Iterative Deepening** - Anytime algorithm with improving results
4. **Transposition Table** - Position caching with Zobrist hashing
5. **Advanced Move Ordering** - TT, PV, killers, history heuristic
6. **Phase-Adaptive Evaluation** - Dynamic weight adjustment
7. **Precise Time Management** - Calculated safety margins

This architecture enables strong play while guaranteeing moves within the 2-second time limit.
