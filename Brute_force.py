from itertools import product

class Futoshiki:
    def __init__(self, N, grid, h_cons, v_cons):
        self.N = N
        self.grid = grid
        self.h_cons = h_cons
        self.v_cons = v_cons



def read_input(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip() != ""]

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


# =========================
# CHECK VALID
# =========================
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
            cons = futo.h_cons[row][col]
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
                    if futo.h_cons[i][j] == 1:
                        line += " < "
                    elif futo.h_cons[i][j] == -1:
                        line += " > "
                    else:
                        line += "   "

            print(line)
            f.write(line + "\n")

            # Vertical
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


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    input_file = "Source/Inputs/input-01.txt"
    output_file = "output-01.txt"

    futo = read_input(input_file)

    if brute_force(futo):
        print("Solved!\n")
        print_output(futo, output_file)
    else:
        print("No solution!")