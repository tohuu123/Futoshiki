from __future__ import annotations

import argparse
from pathlib import Path

from Benchmark import run_benchmark
from Solver import Solver, Method
from parser import parse_futoshiki


SOURCE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SOURCE_DIR.parent
DEFAULT_INPUT = SOURCE_DIR / "Inputs" / "input-01.txt"
DEFAULT_OUTPUT = SOURCE_DIR / "Outputs" / "output-01.txt"
DEFAULT_INPUT_DIR = SOURCE_DIR / "Inputs"
DEFAULT_CSV = PROJECT_ROOT / "Source" / "Outputs" / "benchmark_results.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "Source" / "Outputs" / "benchmark_summary.md"
DEFAULT_CHARTS_DIR = PROJECT_ROOT / "Source" / "Outputs" / "charts"


def resolve_existing_path(path_str: str, *, prefer_source: bool = False) -> Path:
    raw = Path(path_str).expanduser()
    candidates = []
    if raw.is_absolute():
        return raw
    candidates.append(Path.cwd() / raw)
    if prefer_source:
        candidates.append(SOURCE_DIR / raw)
        candidates.append(PROJECT_ROOT / raw)
    else:
        candidates.append(PROJECT_ROOT / raw)
        candidates.append(SOURCE_DIR / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[1].resolve() if len(candidates) > 1 else candidates[0].resolve()


def resolve_output_path(path_str: str | None) -> Path:
    if not path_str:
        return DEFAULT_OUTPUT
    raw = Path(path_str).expanduser()
    if raw.is_absolute():
        return raw
    if raw.parent == Path('.'):
        return (SOURCE_DIR / 'Outputs' / raw.name).resolve()
    return (PROJECT_ROOT / raw).resolve()


def resolve_project_path(path_str: str | None, default_path: Path) -> Path | None:
    if path_str is None:
        return None
    raw = Path(path_str).expanduser()
    if raw.is_absolute():
        return raw
    if path_str == str(default_path):
        return default_path
    return (PROJECT_ROOT / raw).resolve()


def solve_single(args):
    input_path = resolve_existing_path(args.input, prefer_source=True)
    output_path = resolve_output_path(args.output)

    futo = parse_futoshiki(str(input_path))
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
    result.print_result(str(output_path))


def benchmark_cmd(args):
    input_dir = resolve_existing_path(args.input_dir, prefer_source=True)
    csv_path = resolve_project_path(args.csv, DEFAULT_CSV)
    summary_path = resolve_project_path(args.summary, DEFAULT_SUMMARY)
    charts_dir = resolve_project_path(args.charts_dir, DEFAULT_CHARTS_DIR)

    rows = run_benchmark(
        input_dir,
        csv_path,
        summary_path,
        charts_dir=charts_dir,
        max_n_bruteforce=args.max_n_bruteforce,
        max_n_backtracking=args.max_n_backtracking,
        include_backward=args.include_backward,
        outputs_dir=(SOURCE_DIR / "Outputs") if args.write_outputs else None,
    )
    print(f"Saved CSV benchmark to: {csv_path}")
    if summary_path:
        print(f"Saved summary to: {summary_path}")
    if charts_dir:
        print(f"Saved charts to: {charts_dir}")
    print(f"rows={len(rows)}")


def build_parser():
    parser = argparse.ArgumentParser(description="Futoshiki solver CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_solve = sub.add_parser("solve", help="Solve a single puzzle")
    p_solve.add_argument("--input", default=str(DEFAULT_INPUT))
    p_solve.add_argument("--algorithm", choices=["bruteforce", "backtracking", "backward_chaining", "forward_chaining", "astar"], default="astar")
    p_solve.add_argument("--heuristic", choices=["h0", "hrc"], default="hrc")
    p_solve.add_argument("--output", default=str(DEFAULT_OUTPUT))
    p_solve.set_defaults(func=solve_single)

    p_bench = sub.add_parser("benchmark", help="Run benchmark on all inputs")
    p_bench.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR))
    p_bench.add_argument("--csv", default=str(DEFAULT_CSV))
    p_bench.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    p_bench.add_argument("--charts-dir", default=str(DEFAULT_CHARTS_DIR))
    p_bench.add_argument("--max-n-bruteforce", type=int, default=4, help="Skip brute-force for N >= 5 (i.e. above 4x4)")
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
