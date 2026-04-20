from __future__ import annotations

import csv
import math
import time
from pathlib import Path
from statistics import mean
from typing import Dict, List

from parser import parse_futoshiki
from Solver import Solver, Method
from Helper import print_output, write_inference_results_to_file


METRIC_FIELDS = [
    "runtime_sec",
    "peak_memory_kb",
    "expansions",
    "generated",
    "backtracks",
    "inferences",
]


def run_benchmark(
    input_dir: str | Path,
    csv_path: str | Path,
    summary_path: str | Path | None = None,
    charts_dir: str | Path | None = None,
    max_n_bruteforce: int | None = 5,
    max_n_backtracking: int | None = 5,
    include_backward: bool = False,
    outputs_dir: str | Path | None = None,
):
    input_dir = Path(input_dir)
    csv_path = Path(csv_path)
    files = sorted(input_dir.glob("input-*.txt"))
    if not files:
        raise ValueError(f"No input files found in {input_dir}")
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    benchmark_methods = [Method.BRUTE_FORCE, Method.BACKTRACKING, Method.FORWARD_CHAINING, Method.ASTAR]
    if include_backward:
        benchmark_methods.insert(2, Method.BACKWARD_CHAINING)

    total_jobs = len(files) * len(benchmark_methods)
    print(f"[BENCHMARK] Found {len(files)} input files.", flush=True)
    print(f"[BENCHMARK] Methods: {', '.join(m.name for m in benchmark_methods)}", flush=True)
    print(f"[BENCHMARK] Total jobs: {total_jobs}", flush=True)

    rows: List[Dict[str, object]] = []
    fieldnames = [
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
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        f.flush()

        job_index = 0
        for file_path in files:
            file_start = time.perf_counter()
            futo = parse_futoshiki(str(file_path))
            solver = Solver(futo)
            print(f"\n[FILE] {file_path.name} (N={futo.N})", flush=True)

            for method in benchmark_methods:
                job_index += 1
                print(f"[RUN {job_index}/{total_jobs}] {file_path.name} - {method.name} ...", end=" ", flush=True)

                if method == Method.BRUTE_FORCE and max_n_bruteforce is not None and futo.N > max_n_bruteforce:
                    row = _skipped_row(method, file_path.name, futo.N, f"skipped: N>{max_n_bruteforce} for bruteforce")
                    rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print("SKIPPED", flush=True)
                    continue

                if method == Method.BACKTRACKING and max_n_backtracking is not None and futo.N > max_n_backtracking:
                    row = _skipped_row(method, file_path.name, futo.N, f"skipped: N>{max_n_backtracking} for backtracking")
                    rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print("SKIPPED", flush=True)
                    continue

                try:
                    result = solver.solve(method, heuristic_name="hrc") if method == Method.ASTAR else solver.solve(method)
                    row = {
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
                    rows.append(row)
                    writer.writerow(row)
                    f.flush()

                    if outputs_dir is not None and result.success and method not in (Method.FORWARD_CHAINING, Method.BACKWARD_CHAINING):
                        try:
                            stem = Path(file_path.name).stem.replace("input-", "output-")
                            out_name = f"{stem}__{method.name.lower()}.txt"
                            print_output(result.futo, out_name, output_dir=str(outputs_dir), echo_console=False)
                        except Exception as exc:
                            row["notes"] = (row["notes"] + " | " if row["notes"] else "") + f"output write failed: {exc}"

                    if outputs_dir is not None and method in (Method.FORWARD_CHAINING, Method.BACKWARD_CHAINING):
                        try:
                            inferences_dir = Path(outputs_dir) / "Inferences"
                            stem = Path(file_path.name).stem.replace("input-", "output-")
                            inf_name = f"{stem}__{method.name.lower()}.txt"
                            if method == Method.FORWARD_CHAINING and result.inferred is not None:
                                write_inference_results_to_file(result.inferred, futo.N, inferences_dir / inf_name)
                            elif method == Method.BACKWARD_CHAINING:
                                bc_stats = {
                                    k: row[k] for k in ("expansions", "generated", "backtracks", "inferences")
                                }
                                bc_stats["notes"] = str(row.get("notes", ""))
                                _write_bc_inference_file(inferences_dir / inf_name, file_path.name, futo.N, bc_stats)
                        except Exception as exc:
                            row["notes"] = (row["notes"] + " | " if row["notes"] else "") + f"inference write failed: {exc}"

                    print(
                        f"done | solved={result.success} | time={result.elapsed:.4f}s | "
                        f"exp={result.expansions} | inf={result.inferences}",
                        flush=True,
                    )
                except KeyboardInterrupt:
                    row = _skipped_row(method, file_path.name, futo.N, "manually skipped by user (KeyboardInterrupt)")
                    rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print("SKIPPED (manual interrupt)", flush=True)
                    continue

            file_elapsed = time.perf_counter() - file_start
            print(f"[FILE DONE] {file_path.name} in {file_elapsed:.2f}s", flush=True)

    summary = summarize_rows(rows)
    if summary_path is not None:
        write_markdown_summary(summary, rows, summary_path)
        print(f"[WRITE] Summary markdown -> {summary_path}", flush=True)
    if charts_dir is not None:
        write_chart_images(rows, charts_dir)
        print(f"[WRITE] Charts -> {charts_dir}", flush=True)
    return rows


def _write_bc_inference_file(filepath, input_file: str, n: int, bc_stats: dict) -> None:
    """Write backward chaining inference stats to a text file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    sep = "=" * 70
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sep + "\n")
        f.write(f"BACKWARD CHAINING INFERENCE STATS (Size {n}x{n}, Input: {input_file})\n")
        f.write(sep + "\n")
        f.write(f"  Expansions  : {bc_stats.get('expansions', 0)}\n")
        f.write(f"  Generated   : {bc_stats.get('generated', 0)}\n")
        f.write(f"  Backtracks  : {bc_stats.get('backtracks', 0)}\n")
        f.write(f"  Inferences  : {bc_stats.get('inferences', 0)}\n")
        notes = bc_stats.get("notes", "")
        if notes:
            f.write(f"  Notes       : {notes}\n")
        f.write(sep + "\n")


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
                "failed_cases": 0,
                "skipped_cases": len(items),
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
            "failed_cases": sum(1 for item in measured if item["solved"] is False),
            "skipped_cases": sum(1 for item in items if item["solved"] == "SKIPPED"),
            "avg_runtime_sec": mean(float(item["runtime_sec"]) for item in measured),
            "avg_peak_memory_kb": mean(float(item["peak_memory_kb"]) for item in measured),
            "avg_expansions": mean(float(item["expansions"]) for item in measured),
            "avg_generated": mean(float(item["generated"]) for item in measured),
            "avg_backtracks": mean(float(item["backtracks"]) for item in measured),
            "avg_inferences": mean(float(item["inferences"]) for item in measured),
        }
    return summary


def write_markdown_summary(summary: Dict[str, Dict[str, float]], rows: List[Dict[str, object]], path: str | Path) -> None:
    path = Path(path)
    lines = [
        "# Benchmark Summary",
        "",
        "## Average metrics by algorithm",
        "",
        "| Algorithm | Cases | Solved | Failed | Skipped | Avg runtime (s) | Avg peak memory (KB) | Avg expansions | Avg generated | Avg backtracks | Avg inferences |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for algorithm, values in summary.items():
        lines.append(
            "| {algorithm} | {cases} | {solved} | {failed} | {skipped} | {runtime:.6f} | {memory:.2f} | {exp:.2f} | {gen:.2f} | {bt:.2f} | {inf:.2f} |".format(
                algorithm=algorithm,
                cases=int(values["cases"]),
                solved=int(values["solved_cases"]),
                failed=int(values["failed_cases"]),
                skipped=int(values["skipped_cases"]),
                runtime=values["avg_runtime_sec"],
                memory=values["avg_peak_memory_kb"],
                exp=values["avg_expansions"],
                gen=values["avg_generated"],
                bt=values["avg_backtracks"],
                inf=values["avg_inferences"],
            )
        )

    lines += ["", "## Per-test results", ""]
    lines += [
        "| Input | N | Algorithm | Solved | Runtime (s) | Memory (KB) | Expansions | Inferences | Notes |",
        "|---|---:|---|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['input_file']} | {row['n']} | {row['algorithm']} | {row['solved']} | {float(row['runtime_sec']):.6f} | {float(row['peak_memory_kb']):.2f} | {int(row['expansions'])} | {int(row['inferences'])} | {str(row['notes']).replace('|', '/')} |"
        )

    problem_rows = [r for r in rows if r['solved'] in (False, 'SKIPPED') or (r['notes'] not in ('', None))]
    if problem_rows:
        lines += ["", "## Notes on skipped, failed, or conflict-related cases", ""]
        lines += [
            "| Input | Algorithm | Status | Notes |",
            "|---|---|---|---|",
        ]
        for row in problem_rows:
            lines.append(f"| {row['input_file']} | {row['algorithm']} | {row['solved']} | {str(row['notes']).replace('|', '/')} |")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_chart_images(rows: List[Dict[str, object]], charts_dir: str | Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    charts_dir = Path(charts_dir)
    charts_dir.mkdir(parents=True, exist_ok=True)

    algorithms = sorted({str(r['algorithm']) for r in rows})
    inputs = sorted({str(r['input_file']) for r in rows})
    input_to_idx = {name: i for i, name in enumerate(inputs)}

    def _values_for(algorithm: str, metric_key: str):
        vals = [math.nan] * len(inputs)
        for row in rows:
            if str(row['algorithm']) != algorithm:
                continue
            idx = input_to_idx[str(row['input_file'])]
            if row['solved'] == 'SKIPPED':
                vals[idx] = math.nan
            else:
                vals[idx] = float(row[metric_key])
        return vals

    def _line_chart(metric_key: str, title: str, ylabel: str, filename: str) -> None:
        plt.figure(figsize=(12, 6))
        x = list(range(len(inputs)))
        for algorithm in algorithms:
            plt.plot(x, _values_for(algorithm, metric_key), marker='o', label=algorithm)
        plt.xticks(x, inputs, rotation=25, ha='right')
        plt.title(title)
        plt.ylabel(ylabel)
        plt.xlabel('Input file')
        plt.legend()
        plt.tight_layout()
        plt.savefig(charts_dir / filename, dpi=160)
        plt.close()

    _line_chart('runtime_sec', 'Runtime by input', 'Seconds', 'runtime_by_input.png')
    _line_chart('peak_memory_kb', 'Peak memory by input', 'KB', 'memory_by_input.png')
    _line_chart('expansions', 'Expansions by input', 'Count', 'expansions_by_input.png')
    _line_chart('inferences', 'Inferences by input', 'Count', 'inferences_by_input.png')

    x = list(range(len(inputs)))
    metric_specs = [
        ('runtime_sec', 'Runtime by input', 'Seconds'),
        ('peak_memory_kb', 'Peak memory by input', 'KB'),
        ('expansions', 'Expansions by input', 'Count'),
        ('inferences', 'Inferences by input', 'Count'),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True)
    axes = axes.flatten()
    for ax, (metric_key, title, ylabel) in zip(axes, metric_specs):
        for algorithm in algorithms:
            ax.plot(x, _values_for(algorithm, metric_key), marker='o', label=algorithm)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(inputs, rotation=25, ha='right')
        ax.grid(True, alpha=0.25)
    handles, labels = axes[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc='upper center', ncol=max(1, len(algorithms)))
    fig.suptitle('Metrics by input', y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(charts_dir / 'metrics_by_input.png', dpi=160)
    plt.close(fig)

    status_counts = {alg: {'solved': 0, 'failed': 0, 'skipped': 0} for alg in algorithms}
    for row in rows:
        alg = str(row['algorithm'])
        if row['solved'] == 'SKIPPED':
            status_counts[alg]['skipped'] += 1
        elif row['solved'] is True:
            status_counts[alg]['solved'] += 1
        else:
            status_counts[alg]['failed'] += 1

    x = list(range(len(algorithms)))
    solved_vals = [status_counts[a]['solved'] for a in algorithms]
    failed_vals = [status_counts[a]['failed'] for a in algorithms]
    skipped_vals = [status_counts[a]['skipped'] for a in algorithms]

    plt.figure(figsize=(10, 5))
    plt.bar(x, solved_vals, label='Solved')
    plt.bar(x, failed_vals, bottom=solved_vals, label='Failed')
    bottoms = [s + f for s, f in zip(solved_vals, failed_vals)]
    plt.bar(x, skipped_vals, bottom=bottoms, label='Skipped')
    plt.xticks(x, algorithms, rotation=20, ha='right')
    plt.title('Solved / failed / skipped by algorithm')
    plt.ylabel('Number of test cases')
    plt.legend()
    plt.tight_layout()
    plt.savefig(charts_dir / 'status_by_algorithm.png', dpi=160)
    plt.close()
