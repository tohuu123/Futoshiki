from __future__ import annotations

import copy
import heapq
import itertools
from dataclasses import dataclass

from Helper import is_valid


def clone_futo(futo):
    return copy.deepcopy(futo)


def grid_to_tuple(grid):
    return tuple(tuple(row) for row in grid)


def tuple_to_grid(grid_t):
    return [list(row) for row in grid_t]


def apply_grid(futo, grid):
    futo.grid = [row[:] for row in grid]


def count_unassigned(grid):
    return sum(1 for row in grid for value in row if value == 0)


def h_zero(futo, grid):
    return 0


def h_rc(futo, grid):
    row_zeros = [sum(1 for value in row if value == 0) for row in grid]
    col_zeros = [sum(1 for r in range(futo.N) if grid[r][c] == 0) for c in range(futo.N)]
    return max(max(row_zeros, default=0), max(col_zeros, default=0))


HEURISTICS = {
    'h0': h_zero,
    'hrc': h_rc,
}


def get_candidates(futo, grid, row, col):
    if grid[row][col] != 0:
        return [grid[row][col]]

    used = set()
    for j in range(futo.N):
        if grid[row][j] != 0:
            used.add(grid[row][j])
    for i in range(futo.N):
        if grid[i][col] != 0:
            used.add(grid[i][col])

    candidates = []
    for val in range(1, futo.N + 1):
        if val in used:
            continue
        old = grid[row][col]
        grid[row][col] = val
        temp = clone_futo(futo)
        temp.grid = [r[:] for r in grid]
        ok = is_valid(temp, full_check=False)
        grid[row][col] = old
        if ok:
            candidates.append(val)
    return candidates


def has_empty_domain(futo, grid):
    for i in range(futo.N):
        for j in range(futo.N):
            if grid[i][j] == 0 and len(get_candidates(futo, grid, i, j)) == 0:
                return True
    return False


def select_unassigned_cell_mrv(futo, grid):
    best_cell = None
    best_size = None
    best_degree = -1
    for i in range(futo.N):
        for j in range(futo.N):
            if grid[i][j] != 0:
                continue
            size = len(get_candidates(futo, grid, i, j))
            degree = 0
            if j > 0 and grid[i][j-1] == 0: degree += 1
            if j < futo.N - 1 and grid[i][j+1] == 0: degree += 1
            if i > 0 and grid[i-1][j] == 0: degree += 1
            if i < futo.N - 1 and grid[i+1][j] == 0: degree += 1
            if best_size is None or size < best_size or (size == best_size and degree > best_degree):
                best_cell = (i, j)
                best_size = size
                best_degree = degree
    return best_cell


def order_values_lcv(futo, grid, row, col):
    candidates = get_candidates(futo, grid, row, col)
    if len(candidates) <= 1:
        return candidates
    scored = []
    for val in candidates:
        grid[row][col] = val
        score = 0
        for i in range(futo.N):
            for j in range(futo.N):
                if grid[i][j] == 0:
                    score += len(get_candidates(futo, grid, i, j))
        grid[row][col] = 0
        scored.append((score, val))
    scored.sort(reverse=True)
    return [val for _, val in scored]


def is_complete_and_valid(futo, grid):
    if any(v == 0 for row in grid for v in row):
        return False
    temp = clone_futo(futo)
    temp.grid = [row[:] for row in grid]
    return is_valid(temp, full_check=True)


@dataclass(frozen=True)
class Node:
    grid_t: tuple
    g: int
    h: int
    @property
    def f(self):
        return self.g + self.h


def solve_futoshiki_astar(futo, heuristic_name='hrc'):
    heuristic_fn = HEURISTICS[heuristic_name]
    start_grid = [row[:] for row in futo.grid]
    start_t = grid_to_tuple(start_grid)
    start_node = Node(start_t, 0, heuristic_fn(futo, start_grid))

    open_heap = []
    counter = itertools.count()
    heapq.heappush(open_heap, (start_node.f, start_node.h, next(counter), start_node))
    best_g = {start_t: 0}

    stats = {'expansions': 0, 'generated': 0, 'heuristic': heuristic_name}

    while open_heap:
        _, _, _, current = heapq.heappop(open_heap)
        if best_g.get(current.grid_t) != current.g:
            continue

        grid = tuple_to_grid(current.grid_t)
        stats['expansions'] += 1

        if is_complete_and_valid(futo, grid):
            apply_grid(futo, grid)
            return True, stats

        cell = select_unassigned_cell_mrv(futo, grid)
        if cell is None:
            continue
        row, col = cell
        ordered_values = order_values_lcv(futo, grid, row, col)
        stats['generated'] += len(ordered_values)

        for val in ordered_values:
            child = [r[:] for r in grid]
            child[row][col] = val
            temp = clone_futo(futo)
            temp.grid = [r[:] for r in child]
            if not is_valid(temp, full_check=False):
                continue
            if has_empty_domain(futo, child):
                continue
            child_t = grid_to_tuple(child)
            new_g = current.g + 1
            old_g = best_g.get(child_t)
            if old_g is not None and new_g >= old_g:
                continue
            child_h = heuristic_fn(futo, child)
            best_g[child_t] = new_g
            heapq.heappush(open_heap, (new_g + child_h, child_h, next(counter), Node(child_t, new_g, child_h)))

    return False, stats
