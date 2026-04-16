import copy
import time
import tracemalloc
from enum import Enum, auto
from typing import Optional, Set

from Bruteforce import brute_force
from Backtracking import backtracking
from BackwardChaining import solve_futoshiki_with_backward_chaining
from ForwardChaining import solve_futoshiki_forward_chaining
from AStar import solve_futoshiki_astar
from Helper import print_console, print_inference_results, print_output


class Method(Enum):
    BRUTE_FORCE = auto()
    BACKTRACKING = auto()
    BACKWARD_CHAINING = auto()
    FORWARD_CHAINING = auto()
    ASTAR = auto()


class SolveResult:
    def __init__(
        self,
        method: Method,
        success: bool,
        elapsed: float,
        futo,
        inferred: Optional[Set] = None,
        peak_memory_kb: float = 0.0,
        expansions: int = 0,
        generated: int = 0,
        backtracks: int = 0,
        inferences: int = 0,
        notes: str = "",
    ):
        self.method = method
        self.success = success
        self.elapsed = elapsed
        self.futo = futo
        self.inferred = inferred
        self.peak_memory_kb = peak_memory_kb
        self.expansions = expansions
        self.generated = generated
        self.backtracks = backtracks
        self.inferences = inferences
        self.notes = notes

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{self.method.name}] {status} in {self.elapsed:.4f}s"

    def print_result(self, output_file: Optional[str] = None):
        sep = "=" * 70
        status = "SUCCESS" if self.success else "FAILED"
        print(f"\n{sep}")
        print(f"Method : {self.method.name}")
        print(f"Status : {status}")
        print(f"Time   : {self.elapsed:.4f}s")
        print(f"Memory : {self.peak_memory_kb:.2f} KB")
        print(f"Expansions : {self.expansions}")
        print(f"Generated  : {self.generated}")
        print(f"Backtracks : {self.backtracks}")
        print(f"Inferences : {self.inferences}")
        if self.notes:
            print(f"Notes : {self.notes}")
        print(sep)

        if self.success:
            if self.method == Method.FORWARD_CHAINING and self.inferred is not None:
                print_inference_results(self.inferred, self.futo.N)
            else:
                print("\n[Solved Grid]")
                print_console(self.futo)
                if output_file:
                    print_output(self.futo, output_file)
        else:
            print("No solution found.")


class Solver:
    def __init__(self, futo):
        self.futo = futo

    def _snapshot(self):
        return copy.deepcopy(self.futo)

    def _run(self, method: Method, heuristic_name: str = "hrc") -> SolveResult:
        futo = self._snapshot()
        tracemalloc.start()
        start = time.perf_counter()
        inferred = None
        expansions = generated = backtracks = inferences = 0
        notes = ""

        if method == Method.BRUTE_FORCE:
            success = brute_force(futo)

        elif method == Method.BACKTRACKING:
            success = backtracking(futo)

        elif method == Method.BACKWARD_CHAINING:
            success = solve_futoshiki_with_backward_chaining(futo)
            notes = "Backward chaining currently returns only success/failure metrics."

        elif method == Method.FORWARD_CHAINING:
            success, inferred = solve_futoshiki_forward_chaining(futo)
            inferences = len(inferred) if inferred is not None else 0
            notes = "Forward chaining reports inference count; it may not reconstruct a full solved grid."

        elif method == Method.ASTAR:
            success, stats = solve_futoshiki_astar(futo, heuristic_name)
            expansions = stats.get("expansions", 0)
            generated = stats.get("generated", 0)
            notes = f"heuristic={heuristic_name}"

        else:
            raise ValueError(f"Unknown method: {method}")

        elapsed = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return SolveResult(
            method,
            success,
            elapsed,
            futo,
            inferred,
            peak_memory_kb=peak / 1024.0,
            expansions=expansions,
            generated=generated,
            backtracks=backtracks,
            inferences=inferences,
            notes=notes,
        )

    def solve(self, method: Method, heuristic_name: str = "hrc") -> SolveResult:
        return self._run(method, heuristic_name)
