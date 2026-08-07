# Search Algorithms Research

Coursework repo (SMAI — Search Methods in AI) exploring classic AI search algorithms in C++, through two problem domains:

## Othello (`othello/`)

Game-playing bots for Othello/Reversi using adversarial search (minimax with alpha-beta pruning). Includes:
- Own bot implementation(s) tested against reference engines
- Third-party reference engines vendored for benchmarking/sparring: Desdemona, Egaroucid, edax-reversi
- `Othello.pdf` — assignment write-up

## Traveling Salesman Problem (`tsp/`)

Heuristic/local-search solvers for TSP, benchmarked on both Euclidean and non-Euclidean instances of varying size (50/100/200 nodes).

## Notes

This is coursework/research code — it vendors third-party engines for benchmarking and isn't a packaged library. See each subfolder's assignment PDF/README for details.
