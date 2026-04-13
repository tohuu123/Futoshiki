class Futoshiki:
    def __init__(self, N, grid, h_cons, v_cons):
        self.N = N
        self.grid = grid
        self.h_cons = h_cons
        self.v_cons = v_cons


def read_input(filename):
    lines = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if line:
                lines.append(line)

    idx = 0
    N = int(lines[idx])
    idx += 1

    grid = []
    for _ in range(N):
        grid.append(list(map(int, lines[idx].split(','))))
        idx += 1

    h_cons = []
    for _ in range(N):
        h_cons.append(list(map(int, lines[idx].split(','))))
        idx += 1

    v_cons = []
    for _ in range(N - 1):
        v_cons.append(list(map(int, lines[idx].split(','))))
        idx += 1

    return Futoshiki(N, grid, h_cons, v_cons)


def is_valid(futo, full_check=False):
    N = futo.N

    for row in range(N):
        seen = set()
        for col in range(N):
            val = futo.grid[row][col]
            if val == 0:
                continue
            if val in seen:
                return False
            seen.add(val)
        if full_check and len(seen) != N:
            return False

    for col in range(N):
        seen = set()
        for row in range(N):
            val = futo.grid[row][col]
            if val == 0:
                continue
            if val in seen:
                return False
            seen.add(val)
        if full_check and len(seen) != N:
            return False

    for row in range(N):
        for col in range(N - 1):
            cons = futo.h_cons[row][col]
            left = futo.grid[row][col]
            right = futo.grid[row][col + 1]
            if left == 0 or right == 0:
                continue
            if cons == 1 and not (left < right):
                return False
            if cons == -1 and not (left > right):
                return False

    for row in range(N - 1):
        for col in range(N):
            cons = futo.v_cons[row][col]
            up = futo.grid[row][col]
            down = futo.grid[row + 1][col]
            if up == 0 or down == 0:
                continue
            if cons == 1 and not (up < down):
                return False
            if cons == -1 and not (up > down):
                return False

    return True


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


def backtracking(futo):
    cell = select_unassigned_cell_mrv(futo)
    if cell is None:
        return is_valid(futo, full_check=True)

    row, col = cell
    candidates = order_values_lcv(futo, row, col)
    for val in candidates:
        futo.grid[row][col] = val
        if not has_empty_domain(futo) and backtracking(futo):
            return True
        futo.grid[row][col] = 0
    return False


def print_output(futo, filename):
    with open(filename, 'w') as f:
        for i in range(futo.N):
            line = ""
            for j in range(futo.N):
                line += str(futo.grid[i][j])
                if j < futo.N - 1:
                    if futo.h_cons[i][j] == 1:
                        line += " < "
                    elif futo.h_cons[i][j] == -1:
                        line += " > "
                    else:
                        line += "   "
            print(line)
            f.write(line + "\n")

            if i < futo.N - 1:
                line = ""
                for j in range(futo.N):
                    if futo.v_cons[i][j] == 1:
                        line += "^"
                    elif futo.v_cons[i][j] == -1:
                        line += "v"
                    else:
                        line += " "
                    if j < futo.N - 1:
                        line += "   "
                print(line)
                f.write(line + "\n")


if __name__ == "__main__":
    input_file = "Source/Inputs/input-01.txt"
    output_file = "output-01.txt"

    futo = read_input(input_file)

    if backtracking(futo):
        print("Solved!\n")
        print_output(futo, output_file)
    else:
        print("No solution!")
