from __future__ import annotations

import argparse

from Solver import Solver, Method
from parser import parse_futoshiki


def solve_single(args):
    futo = parse_futoshiki(args.input)
    solver = Solver(futo)
    method_map = {
        "bruteforce": Method.BRUTE_FORCE,
        "backtracking": Method.BACKTRACKING,
        "backward_chaining": Method.BACKWARD_CHAINING,
        "forward_chaining": Method.FORWARD_CHAINING,
        "astar": Method.ASTAR,
    }
    method = method_map[args.algorithm]
    result = solver.solve(method, heuristic_name=args.heuristic if method == Method.ASTAR else "hrc")
    result.print_result(args.output)


def build_parser():
    parser = argparse.ArgumentParser(description="Futoshiki main package + A* integration")
    p_solve = parser.add_subparsers(dest="command", required=True)

    solve = p_solve.add_parser("solve", help="Solve a single puzzle")
    solve.add_argument("--input", default="Inputs/input-01.txt")
    solve.add_argument("--algorithm", choices=["bruteforce", "backtracking", "backward_chaining", "forward_chaining", "astar"], default="astar")
    solve.add_argument("--heuristic", choices=["h0", "hrc"], default="hrc")
    solve.add_argument("--output", default="output-01.txt")
    solve.set_defaults(func=solve_single)

    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
