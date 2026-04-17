from itertools import product
from Helper import is_valid


def brute_force(futo, stats=None):
    empty_cells = []

    for i in range(futo.N):
        for j in range(futo.N):
            if futo.grid[i][j] == 0:
                empty_cells.append((i, j))

    domain = range(1, futo.N + 1)

    for values in product(domain, repeat=len(empty_cells)):
        if stats is not None:
            stats["expansions"] += 1
        for idx, (i, j) in enumerate(empty_cells):
            futo.grid[i][j] = values[idx]
        if is_valid(futo, full_check=True):
            return True

    for i, j in empty_cells:
        futo.grid[i][j] = 0

    return False
