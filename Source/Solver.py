import copy
import time
from enum import Enum, auto
from typing import Optional, Set

from Bruteforce import brute_force
from Backtracking import backtracking
from BackwardChaining import solve_futoshiki_with_backward_chaining
from ForwardChaining import solve_futoshiki_forward_chaining
from Helper import *


class Method(Enum):
    BRUTE_FORCE       = auto()
    BACKTRACKING      = auto()
    BACKWARD_CHAINING = auto()
    FORWARD_CHAINING  = auto()

class SolveResult:
    def __init__(self, method: Method, success: bool, elapsed: float,
                 futo, inferred: Optional[Set] = None):
        self.method   = method
        self.success  = success
        self.elapsed  = elapsed
        self.futo     = futo
        self.inferred = inferred

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
        print(sep)

        if self.success:
            if self.method == Method.FORWARD_CHAINING and self.inferred is not None:
                print_inference_results(self.inferred, self.futo.N)
            else:
                print("\n[Solved Grid]")
                print_console(self.futo)
        else:
            print("No solution found.")


class Solver:
    def __init__(self, futo):
        self.futo = futo

    def _snapshot(self):
        snap = copy.deepcopy(self.futo)
        return snap

    def _run(self, method: Method) -> SolveResult:
        futo = self._snapshot()
        start = time.perf_counter()

        if method == Method.BRUTE_FORCE:
            success  = brute_force(futo)
            inferred = None

        elif method == Method.BACKTRACKING:
            success  = backtracking(futo)
            inferred = None

        elif method == Method.BACKWARD_CHAINING:
            success  = solve_futoshiki_with_backward_chaining(futo)
            inferred = None

        elif method == Method.FORWARD_CHAINING:
            success, inferred = solve_futoshiki_forward_chaining(futo)

        else:
            raise ValueError(f"Unknown method: {method}")

        elapsed = time.perf_counter() - start
        return SolveResult(method, success, elapsed, futo, inferred)

    def solve(self, method: Method) -> SolveResult:
        return self._run(method)

    def solve_brute_force(self) -> SolveResult:
        return self._run(Method.BRUTE_FORCE)

    def solve_backtracking(self) -> SolveResult:
        return self._run(Method.BACKTRACKING)

    def solve_backward_chaining(self) -> SolveResult:
        return self._run(Method.BACKWARD_CHAINING)

    def solve_forward_chaining(self) -> SolveResult:
        return self._run(Method.FORWARD_CHAINING)

    def compare_all(self, output_file: Optional[str] = None) -> list[SolveResult]:
        results = []
        for method in Method:
            result = self._run(method)
            result.print_result(output_file)
            results.append(result)
        return results
