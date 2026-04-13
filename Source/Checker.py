# check the solution is valid or not
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