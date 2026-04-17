from __future__ import annotations

import argparse

from Benchmark import run_benchmark
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


def benchmark_cmd(args):
    rows = run_benchmark(
        args.input_dir,
        args.csv,
        args.summary,
        charts_dir=args.charts_dir,
        max_n_bruteforce=args.max_n_bruteforce,
        max_n_backtracking=args.max_n_backtracking,
        include_backward=args.include_backward,
        outputs_dir="Source/Outputs" if args.write_outputs else None,
    )
    print(f"Saved CSV benchmark to: {args.csv}")
    if args.summary:
        print(f"Saved summary to: {args.summary}")
    if args.charts_dir:
        print(f"Saved charts to: {args.charts_dir}")
    print(f"rows={len(rows)}")


def build_parser():
    parser = argparse.ArgumentParser(description="Futoshiki main package + A* + benchmark integration")
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="Solve a single puzzle")
    p_solve.add_argument("--input", default="Inputs/input-01.txt")
    p_solve.add_argument("--algorithm", choices=["bruteforce", "backtracking", "backward_chaining", "forward_chaining", "astar"], default="astar")
    p_solve.add_argument("--heuristic", choices=["h0", "hrc"], default="hrc")
    p_solve.add_argument("--output", default="output-01.txt")
    p_solve.set_defaults(func=solve_single)

    p_bench = sub.add_parser("benchmark", help="Run benchmark on all inputs")
    p_bench.add_argument("--input-dir", default="Inputs")
    p_bench.add_argument("--csv", default="Docs/benchmark_results.csv")
    p_bench.add_argument("--summary", default="Docs/benchmark_summary.md")
    p_bench.add_argument("--charts-dir", default="Docs/charts")
    p_bench.add_argument("--max-n-bruteforce", type=int, default=5, help="Skip brute-force above this board size")
    p_bench.add_argument("--max-n-backtracking", type=int, default=5, help="Skip backtracking above this board size")
    p_bench.add_argument(
        "--include-backward",
        dest="include_backward",
        action="store_true",
        default=True,
        help="Include backward chaining in benchmark (default: enabled)",
    )
    p_bench.add_argument(
        "--exclude-backward",
        dest="include_backward",
        action="store_false",
        help="Exclude backward chaining from benchmark",
    )
    p_bench.add_argument(
        "--write-outputs",
        action="store_true",
        help="Write solved benchmark grids to Source/Outputs",
    )
    p_bench.set_defaults(func=benchmark_cmd)
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
