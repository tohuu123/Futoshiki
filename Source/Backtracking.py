from Helper import is_valid


def get_candidates(futo, row, col):
    if futo.grid[row][col] != 0:
        return [futo.grid[row][col]]

    used = set()
    for j in range(futo.N):
        if futo.grid[row][j] != 0:
            used.add(futo.grid[row][j])
    for i in range(futo.N):
        if futo.grid[i][col] != 0:
            used.add(futo.grid[i][col])

    candidates = []
    for val in range(1, futo.N + 1):
        if val in used:
            continue
        futo.grid[row][col] = val
        ok = is_valid(futo, full_check=False)
        futo.grid[row][col] = 0
        if ok:
            candidates.append(val)
    return candidates


def select_unassigned_cell_mrv(futo):
    best_cell = None
    best_size = None
    for i in range(futo.N):
        for j in range(futo.N):
            if futo.grid[i][j] != 0:
                continue
            size = len(get_candidates(futo, i, j))
            if best_size is None or size < best_size:
                best_size = size
                best_cell = (i, j)
    return best_cell


def order_values_lcv(futo, row, col):
    candidates = get_candidates(futo, row, col)
    if len(candidates) <= 1:
        return candidates

    scored = []
    for val in candidates:
        futo.grid[row][col] = val
        score = 0
        for i in range(futo.N):
            for j in range(futo.N):
                if futo.grid[i][j] == 0:
                    score += len(get_candidates(futo, i, j))
        futo.grid[row][col] = 0
        scored.append((score, val))

    scored.sort(reverse=True)
    return [val for _, val in scored]


def has_empty_domain(futo):
    for i in range(futo.N):
        for j in range(futo.N):
            if futo.grid[i][j] == 0 and len(get_candidates(futo, i, j)) == 0:
                return True
    return False


def backtracking(futo, stats=None):
    if stats is not None:
        stats["expansions"] += 1

    cell = select_unassigned_cell_mrv(futo)
    if cell is None:
        return is_valid(futo, full_check=True)

    row, col = cell
    candidates = order_values_lcv(futo, row, col)
    if stats is not None:
        stats["generated"] += len(candidates)

    for val in candidates:
        futo.grid[row][col] = val
        if not has_empty_domain(futo) and backtracking(futo, stats):
            return True
        futo.grid[row][col] = 0

    if stats is not None:
        stats["backtracks"] += 1
    return False
