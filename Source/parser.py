from typing import List
from Source.Brute_force import *

class FutoshikiInput:
    def __init__(
        self,
        N: int,
        grid: List[List[int]],
        h_constraints: List[List[int]],
        v_constraints: List[List[int]],
    ):
        self.N = N
        self.grid = grid
        self.h_constraints = h_constraints
        self.v_constraints = v_constraints

    def __repr__(self):
        return (
            f"N={self.N}\n"
            f"Grid={self.grid}\n"
            f"H={self.h_constraints}\n"
            f"V={self.v_constraints}"
        )
    def get_givens(self): 
        givens = []
        for i in range(self.N):
            for j in range(self.N):
                val = self.grid[i][j]
                if val != 0:
                    givens.append((i + 1, j + 1, val))
        return givens
    def get_lessH_facts(self):
        H = self.h_constraints
        lessH_facts = set() 
        for i in range(len(H)):
            for j in range(len(H[i])):
                if H[i][j] == 1:
                   lessH_facts.add((i + 1, j + 1))
        return lessH_facts
    def get_greaterH_facts(self):
        H = self.h_constraints
        lessH_facts = set()
        for i in range(len(H)):
            for j in range(len(H[i])):
                if H[i][j] == -1:
                   lessH_facts.add((i + 1, j + 1))
        return lessH_facts
    def get_lessV_facts(self):
        V = self.v_constraints
        lessV_facts = set()
        for i in range(len(V)):
            for j in range(len(V[i])):
                if V[i][j] == 1:
                   lessV_facts.add((i + 1, j + 1))
        return lessV_facts
    def get_greaterV_facts(self):
        V = self.v_constraints
        greaterV_facts = set()
        for i in range(len(V)):
            for j in range(len(V[i])):
                if V[i][j] == -1:
                   greaterV_facts.add((i + 1, j + 1))
        return greaterV_facts

def _clean_lines(filepath: str):
    """Remove comments and empty lines."""
    lines = []
    with open(filepath, "r") as f:
        for line in f:
            # Remove comments
            line = line.split("#")[0].strip()
            if line:
                lines.append(line)
    return lines


def _parse_row(line: str):
    return [int(x.strip()) for x in line.split(",")]


def _parse_header(lines: List[str]):
    """Parse first-line header.

    Supported format:
    - n,grid_rows,h_rows,v_rows
    """
    if not lines:
        return None, lines

    first = lines[0]
    try:
        if "," in first:
            values = _parse_row(first)
        else:
            values = [int(first.strip())]
    except ValueError:
        return None, lines

    if not values:
        return None, lines

    n = values[0]
    section_defaults = [n, n, n - 1]  # grid_rows, h_rows, v_rows
    overrides = values[1:]

    if len(overrides) > len(section_defaults):
        return None, lines

    for i, value in enumerate(overrides):
        section_defaults[i] = value

    grid_rows, h_rows, v_rows = section_defaults
    return (n, grid_rows, h_rows, v_rows), lines[1:]


def _extract_data_lines(lines: List[str]) -> List[str]:
    """Keep only comma-separated numeric rows, skipping headers"""
    data_lines = []
    for line in lines:
        if "," not in line:
            continue
        _parse_row(line)  # Validate row format early.
        data_lines.append(line)
    return data_lines

# only check input
def check_futoshiki(header, data_lines): 
    if not data_lines:
        raise ValueError("Input file does not contain any data rows")

    if header is None:
        raise ValueError("Invalid header")
    
    n, grid_rows, h_rows, v_rows = header

    if n <= 0 or grid_rows <= 0 or h_rows < 0 or v_rows < 0:
        raise ValueError("Header values must be non-negative, and n/grid_rows > 0")
    
    expected_rows = grid_rows + h_rows + v_rows
    if len(data_lines) != expected_rows:
        raise ValueError(
            f"Invalid number of data rows: expected {expected_rows}, got {len(data_lines)}"
        )

    if grid_rows != n:
        raise ValueError("grid_rows must be equal to n")
    return True

# parser function 
def parse_futoshiki(filepath: str):
    lines = _clean_lines(filepath)
    header, remaining_lines = _parse_header(lines)
    data_lines = _extract_data_lines(remaining_lines)
    
    # checker function
    check_futoshiki(header, data_lines)

    n, grid_rows, h_rows, v_rows = header
    idx = 0

    # ---- GRID ----
    grid = []
    for _ in range(grid_rows):
        row = _parse_row(data_lines[idx])
        if len(row) != n:
            raise ValueError("Invalid grid row length")
        grid.append(row)
        idx += 1

    # ---- HORIZONTAL CONSTRAINTS ----
    h_constraints = []
    for _ in range(h_rows):
        row = _parse_row(data_lines[idx])
        if len(row) != n - 1:
            raise ValueError("Invalid horizontal constraint row length")
        h_constraints.append(row)
        idx += 1

    # ---- VERTICAL CONSTRAINTS ----
    v_constraints = []
    for _ in range(v_rows):
        row = _parse_row(data_lines[idx])
        if len(row) != n:
            raise ValueError("Invalid vertical constraint row length")
        v_constraints.append(row)
        idx += 1

    return FutoshikiInput(n, grid, h_constraints, v_constraints)
