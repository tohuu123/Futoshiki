# Futoshiki Solver - How to Run

## Prerequisites

```bash
python -m venv .venv
source .venv/bin/activate      
pip install -r requirements.txt
```

---

## I. Running CLI benchmarks

## Step 1 — Prepare a folder with only the three test cases:

Prepare the three input files you want to benchmark into a ```Source/Outputs``` folder:

For example: `input-01.txt`, `input-05.txt`, `input-09.txt` with whichever three files you want.

---

## Step 2 — Run the benchmark:

```bash
python Source/main.py benchmark \
  --input-dir Source/Inputs/ \
  --csv     Source/Outputs/benchmark_results.csv \
  --summary Source/Outputs/benchmark_summary.md \
  --charts-dir Source/Outputs/charts \
  --max-n-bruteforce 4 \
  --max-n-backtracking 5 \
  --write-outputs
```

**What each flag does:**

| Flag | Effect |
|---|---|
| `--input-dir` | Folder containing the three chosen input files |
| `--csv` | CSV file with raw per-run metrics |
| `--summary` | Markdown table summarising all results |
| `--charts-dir` | Folder for all generated PNG charts |
| `--max-n-bruteforce 4` | Skip brute-force on grids larger than 4×4 |
| `--max-n-backtracking 5` | Skip backtracking on grids larger than 5×5 |
| `--write-outputs` | Write solved grids to `Source/Outputs/` |

> To include backward chaining add `--include-backward`.  
> To exclude it add `--exclude-backward`.

---

## Step 3 — Find the results:

After the run completes, all output is inside `Source/Outputs/`:

| Path | Content |
|---|---|
| `Source/Outputs/benchmark_results.csv` | Raw metrics (one row per algorithm × input) |
| `Source/Outputs/benchmark_summary.md` | Human-readable markdown summary table |
| `Source/Outputs/charts/runtime_by_input.png` | Runtime chart |
| `Source/Outputs/charts/memory_by_input.png` | Peak memory chart |
| `Source/Outputs/charts/expansions_by_input.png` | Node expansions chart |
| `Source/Outputs/charts/inferences_by_input.png` | Inferences chart |
| `Source/Outputs/charts/metrics_by_input.png` | Combined 2×2 chart (all four metrics) |
| `Source/Outputs/charts/status_by_algorithm.png` | Solved / failed / skipped bar chart |
| `Source/Outputs/<stem>__<algorithm>.txt` | Solved grid text files (with `--write-outputs`) |

## II. Running the GUI of the project:
```bash
python Source/gui.py
```
