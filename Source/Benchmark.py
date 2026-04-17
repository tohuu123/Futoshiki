from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean
from typing import Dict, List

from Helper import is_valid, print_output
from parser import parse_futoshiki
from Solver import Solver, Method


def run_benchmark(
    input_dir: str | Path,
    csv_path: str | Path,
    summary_path: str | Path | None = None,
    charts_dir: str | Path | None = None,
    outputs_dir: str | Path | None = None,
    max_n_bruteforce: int | None = 5,
    max_n_backtracking: int | None = 5,
    include_backward: bool = True,
):
    input_dir = Path(input_dir)
    csv_path = Path(csv_path)
    outputs_path = Path(outputs_dir) if outputs_dir is not None else None
    files = sorted(input_dir.glob("input-*.txt"))
    if not files:
        raise ValueError(f"No input files found in {input_dir}")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    if outputs_path is not None:
        outputs_path.mkdir(parents=True, exist_ok=True)

    benchmark_methods = [Method.BRUTE_FORCE, Method.BACKTRACKING, Method.FORWARD_CHAINING, Method.ASTAR]
    if include_backward:
        benchmark_methods.insert(2, Method.BACKWARD_CHAINING)

    rows: List[Dict[str, object]] = []
    for file_path in files:
        futo = parse_futoshiki(str(file_path))
        solver = Solver(futo)
        for method in benchmark_methods:
            if method == Method.BRUTE_FORCE and max_n_bruteforce is not None and futo.N > max_n_bruteforce:
                rows.append(_skipped_row(method, file_path.name, futo.N, f"skipped: N>{max_n_bruteforce} for bruteforce"))
                continue
            if method == Method.BACKTRACKING and max_n_backtracking is not None and futo.N > max_n_backtracking:
                rows.append(_skipped_row(method, file_path.name, futo.N, f"skipped: N>{max_n_backtracking} for backtracking"))
                continue

            result = solver.solve(method, heuristic_name="hrc") if method == Method.ASTAR else solver.solve(method)
            rows.append(
                {
                    "algorithm": method.name,
                    "input_file": file_path.name,
                    "n": futo.N,
                    "solved": result.success,
                    "runtime_sec": round(result.elapsed, 6),
                    "peak_memory_kb": round(result.peak_memory_kb, 2),
                    "expansions": result.expansions,
                    "generated": result.generated,
                    "backtracks": result.backtracks,
                    "inferences": result.inferences,
                    "notes": result.notes,
                }
            )
            if outputs_path is not None and result.success and is_valid(result.futo, full_check=True):
                output_file = _benchmark_output_name(file_path, method)
                print_output(result.futo, output_file, output_dir=str(outputs_path), echo_console=False)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "algorithm",
                "input_file",
                "n",
                "solved",
                "runtime_sec",
                "peak_memory_kb",
                "expansions",
                "generated",
                "backtracks",
                "inferences",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize_rows(rows)
    if summary_path is not None:
        write_markdown_summary(summary, summary_path)
    if charts_dir is not None:
        write_chart_images(summary, charts_dir)
    return rows


def _skipped_row(method: Method, input_file: str, n: int, note: str) -> Dict[str, object]:
    return {
        "algorithm": method.name,
        "input_file": input_file,
        "n": n,
        "solved": "SKIPPED",
        "runtime_sec": 0.0,
        "peak_memory_kb": 0.0,
        "expansions": 0,
        "generated": 0,
        "backtracks": 0,
        "inferences": 0,
        "notes": note,
    }


def _benchmark_output_name(file_path: Path, method: Method) -> str:
    match = re.match(r"^input-(\d+)$", file_path.stem)
    if match:
        return f"output-{match.group(1)}__{method.name.lower()}.txt"
    return f"output-{file_path.stem}__{method.name.lower()}.txt"


def summarize_rows(rows: List[Dict[str, object]]) -> Dict[str, Dict[str, float]]:
    grouped: Dict[str, List[Dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["algorithm"]), []).append(row)
    summary: Dict[str, Dict[str, float]] = {}
    for algorithm, items in grouped.items():
        measured = [item for item in items if item["solved"] != "SKIPPED"]
        if not measured:
            summary[algorithm] = {
                "cases": len(items),
                "solved_cases": 0,
                "avg_runtime_sec": 0.0,
                "avg_peak_memory_kb": 0.0,
                "avg_expansions": 0.0,
                "avg_generated": 0.0,
                "avg_backtracks": 0.0,
                "avg_inferences": 0.0,
            }
            continue
        summary[algorithm] = {
            "cases": len(items),
            "solved_cases": sum(1 for item in measured if item["solved"] is True),
            "avg_runtime_sec": mean(float(item["runtime_sec"]) for item in measured),
            "avg_peak_memory_kb": mean(float(item["peak_memory_kb"]) for item in measured),
            "avg_expansions": mean(float(item["expansions"]) for item in measured),
            "avg_generated": mean(float(item["generated"]) for item in measured),
            "avg_backtracks": mean(float(item["backtracks"]) for item in measured),
            "avg_inferences": mean(float(item["inferences"]) for item in measured),
        }
    return summary


def write_markdown_summary(summary: Dict[str, Dict[str, float]], path: str | Path) -> None:
    path = Path(path)
    lines = [
        "# Benchmark Summary",
        "",
        "| Algorithm | Cases | Solved | Avg runtime (s) | Avg peak memory (KB) | Avg expansions | Avg generated | Avg backtracks | Avg inferences |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for algorithm, values in summary.items():
        lines.append(
            "| {algorithm} | {cases} | {solved} | {runtime:.6f} | {memory:.2f} | {exp:.2f} | {gen:.2f} | {bt:.2f} | {inf:.2f} |".format(
                algorithm=algorithm,
                cases=int(values["cases"]),
                solved=int(values["solved_cases"]),
                runtime=values["avg_runtime_sec"],
                memory=values["avg_peak_memory_kb"],
                exp=values["avg_expansions"],
                gen=values["avg_generated"],
                bt=values["avg_backtracks"],
                inf=values["avg_inferences"],
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_chart_images(summary: Dict[str, Dict[str, float]], charts_dir: str | Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)
    algorithms = list(summary.keys())

    def _bar(metric_key: str, title: str, ylabel: str, filename: str) -> None:
        values = [summary[name][metric_key] for name in algorithms]
        plt.figure(figsize=(10, 5))
        plt.bar(algorithms, values)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xticks(rotation=20, ha="right")
        plt.tight_layout()
        plt.savefig(charts_dir / filename, dpi=160)
        plt.close()

    _bar("avg_runtime_sec", "Average Runtime by Algorithm", "Seconds", "avg_runtime.png")
    _bar("avg_peak_memory_kb", "Average Peak Memory by Algorithm", "KB", "avg_peak_memory.png")
    _bar("avg_expansions", "Average Expansions by Algorithm", "Count", "avg_expansions.png")
