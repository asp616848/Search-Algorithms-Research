import numpy as np

def read_input(file_path):
    with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
        raw_lines = f.readlines()


    # Strip \x00, newlines, spaces, and skip empty lines
    lines = []
    for line in raw_lines:
        clean = line.replace("\x00", "").strip()
        if clean != "":
            lines.append(clean)

    metric = lines[0]
    n = int(lines[1])  # should now be "50"

    matrix = []
    for i in range(2, 2 + n):
        row = list(map(float, lines[i].split()))
        matrix.append(row)

    return metric, n, np.array(matrix)


def write_tour(file_path, tour):
    with open(file_path, 'a') as f:
        f.write(" ".join(map(str, tour)) + "\n")

def compute_cost(tour, dist_matrix):
    # vectorized cost computation using numpy indexing
    # ensure tour is a numpy array of ints
    import numpy as _np
    t = _np.asarray(tour, dtype=int)
    if t.size == 0:
        return 0.0
    next_idx = _np.roll(t, -1)
    # dist_matrix can be numpy array; indexing with arrays gives elementwise distances
    cost = dist_matrix[t, next_idx].sum()
    return float(cost)
