from itertools import product

def is_valid(futo, full_check=False):
    N = futo.N

    # Row check
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

    # Column check
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

    # Horizontal constraints
    for row in range(N):
        for col in range(N - 1):
            cons = futo.h_constraints[row][col]
            left = futo.grid[row][col]
            right = futo.grid[row][col + 1]

            if left == 0 or right == 0:
                continue

            if cons == 1 and not (left < right):
                return False
            if cons == -1 and not (left > right):
                return False

    # Vertical constraints
    for row in range(N - 1):
        for col in range(N):
            cons = futo.v_constraints[row][col]
            up = futo.grid[row][col]
            down = futo.grid[row + 1][col]

            if up == 0 or down == 0:
                continue

            if cons == 1 and not (up < down):
                return False
            if cons == -1 and not (up > down):
                return False

    return True

def brute_force(futo):
    empty_cells = []

    for i in range(futo.N):
        for j in range(futo.N):
            if futo.grid[i][j] == 0:
                empty_cells.append((i, j))

    domain = range(1, futo.N + 1)

    for values in product(domain, repeat=len(empty_cells)):
        for idx, (i, j) in enumerate(empty_cells):
            futo.grid[i][j] = values[idx]
        if is_valid(futo, full_check=True):
            return True

    for i, j in empty_cells:
        futo.grid[i][j] = 0

    return False

def print_output(futo, filename):
    with open(filename, 'w') as f:
        for i in range(futo.N):

            # Row
            line = ""
            for j in range(futo.N):
                line += str(futo.grid[i][j])

                if j < futo.N - 1:
                    if futo.h_constraints[i][j] == 1:
                        line += " < "
                    elif futo.h_constraints[i][j] == -1:
                        line += " > "
                    else:
                        line += "   "

            print(line)
            f.write(line + "\n")

            # Vertical
            if i < futo.N - 1:
                line = ""
                for j in range(futo.N):
                    if futo.v_constraints[i][j] == 1:
                        line += "^"
                    elif futo.v_constraints[i][j] == -1:
                        line += "v"
                    else:
                        line += " "

                    if j < futo.N - 1:
                        line += "   "

                print(line)
                f.write(line + "\n")