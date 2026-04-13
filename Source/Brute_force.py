from itertools import product
import os
from Source.Checker import is_valid 

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
    fullpath = os.path.join("Source/Outputs", filename)
    with open(fullpath, 'w') as f:
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