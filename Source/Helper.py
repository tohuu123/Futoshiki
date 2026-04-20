from pathlib import Path
import os 

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

def print_output(futo, filename, output_dir="Outputs", echo_console=True):
    filename_path = Path(filename)
    if filename_path.is_absolute() or filename_path.parent != Path('.'):
        fullpath = filename_path
    else:
        fullpath = Path(output_dir) / filename_path

    fullpath.parent.mkdir(parents=True, exist_ok=True)
    with open(fullpath, 'w', encoding='utf-8') as f:
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

            if echo_console:
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

                if echo_console:
                    print(line)
                f.write(line + "\n")

def print_console(futo):
    for i in range(futo.N):
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

def print_inference_results(inferred_facts, N):
    positive_vals = []
    negated_vals = []
    other_facts = []

    for fact in sorted(list(inferred_facts)):
        if fact.startswith("Not_Val_"):
            negated_vals.append(fact)
        elif fact.startswith("Val_"):
            positive_vals.append(fact)
        else:
            other_facts.append(fact)

    cell_domains = {}
    for i in range(1, N + 1):
        for j in range(1, N + 1):
            pos_v = [int(f.split("_")[3]) for f in positive_vals if f.startswith(f"Val_{i}_{j}_")]
            if pos_v:
                cell_domains[(i, j)] = pos_v
            else:
                excluded = {int(f.split("_")[4]) for f in negated_vals if f.startswith(f"Not_Val_{i}_{j}_")}
                cell_domains[(i, j)] = [v for v in range(1, N + 1) if v not in excluded]

    sep = "=" * 70
    print(sep)
    print(f"INFERENCE RESULTS (Size {N}x{N})")
    print(sep)

    print(f"\n[Positive Val facts] ({len(positive_vals)} facts)")
    for f in positive_vals:
        print(f"  + {f}")

    print("\n[Cell domains after inference]")
    for (i, j), domain in sorted(cell_domains.items()):
        status = "pinned" if len(domain) == 1 else ""
        print(f"  Cell({i},{j}): {domain}  {status}")

    print(f"\n[Negated Val facts / eliminations] ({len(negated_vals)} facts)")
    for f in negated_vals:
        print(f"  - {f}")
    print(f"\n[Other inferred facts] ({len(other_facts)} facts)")
    for f in other_facts:
        print(f"  ~ {f}")

    print(f"\nTotal inferred facts: {len(inferred_facts)}")
    print(sep)