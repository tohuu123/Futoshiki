from __future__ import annotations
from itertools import product as iproduct
from typing import List, Set, FrozenSet, Tuple
from dataclasses import dataclass, field

class Literal:
    def __init__(self, pred: str, args: Tuple, negated: bool = False):
        self.pred    = pred
        self.args    = args
        self.negated = negated

    def __neg__(self) -> "Literal":
        return Literal(self.pred, self.args, not self.negated)

    def __eq__(self, other) -> bool:
        return (isinstance(other, Literal)
                and self.pred    == other.pred
                and self.args    == other.args
                and self.negated == other.negated)

    def __hash__(self) -> int:
        return hash((self.pred, self.args, self.negated))

    def __str__(self) -> str:
        sign = "¬" if self.negated else ""
        args = ",".join(map(str, self.args))
        return f"{sign}{self.pred}({args})"

    def atom(self) -> "Literal":
        return Literal(self.pred, self.args, False)


Clause = FrozenSet[Literal]

def clause(lits: List[Literal]) -> Clause:
    return frozenset(lits)

def neg(lit: Literal) -> Literal:
    return -lit

def _Val(i, j, v, negated=False) -> Literal: return Literal("Val",      (i, j, v), negated)
def _LH (i, j, negated=False)    -> Literal: return Literal("LessH",    (i, j),    negated)
def _GH (i, j, negated=False)    -> Literal: return Literal("GreaterH", (i, j),    negated)
def _LV (i, j, negated=False)    -> Literal: return Literal("LessV",    (i, j),    negated)
def _GrV(i, j, negated=False)    -> Literal: return Literal("GreaterV", (i, j),    negated)


@dataclass
class GroundKB:
    cell_clauses:   List[Clause] = field(default_factory=list)
    unique_clauses: List[Clause] = field(default_factory=list)
    ineq_clauses:   List[Clause] = field(default_factory=list)
    given_clauses:  List[Clause] = field(default_factory=list)
    all_clauses:    List[Clause] = field(default_factory=list)


class GroundKBGenerator:
    def __init__(self, N: int):
        self.N      = N
        self.domain = list(range(1, N + 1))
        self.cells  = [(i, j) for i in self.domain for j in self.domain]

    def _axiom_A1(self) -> List[Clause]:
        return [frozenset(_Val(i, j, v) for v in self.domain)
                for i, j in self.cells]

    def _axiom_A2(self) -> List[Clause]:
        clauses = []
        for i, j in self.cells:
            for v1, v2 in iproduct(self.domain, repeat=2):
                if v1 < v2:
                    clauses.append(frozenset([_Val(i, j, v1, True),
                                              _Val(i, j, v2, True)]))
        return clauses

    def _axiom_A3(self) -> List[Clause]:    
        clauses = []
        for i in self.domain:
            for v in self.domain:
                for j1, j2 in iproduct(self.domain, repeat=2):
                    if j1 < j2:
                        clauses.append(frozenset([_Val(i, j1, v, True),
                                                  _Val(i, j2, v, True)]))
        return clauses

    def _axiom_A4(self) -> List[Clause]:
        clauses = []
        for j in self.domain:
            for v in self.domain:
                for i1, i2 in iproduct(self.domain, repeat=2):
                    if i1 < i2:
                        clauses.append(frozenset([_Val(i1, j, v, True),
                                                  _Val(i2, j, v, True)]))
        return clauses

    def _axiom_A5(self, givens: List[Tuple[int, int, int]]) -> List[Clause]:
        clauses = []
        for (i, j, v) in givens:
            clauses.append(frozenset([_Val(i, j, v)]))
            for v2 in self.domain:
                if v2 != v:
                    clauses.append(frozenset([_Val(i, j, v2, True)]))
        return clauses

    def _axiom_A6(self, lessH: Set[Tuple[int, int]]) -> List[Clause]:
        clauses = []
        for (i, j) in lessH:
            if j + 1 > self.N:
                continue
            for v1, v2 in iproduct(self.domain, repeat=2):
                if v1 >= v2:
                    clauses.append(frozenset([_LH(i, j,     True),
                                              _Val(i, j,   v1, True),
                                              _Val(i, j+1, v2, True)]))
        return clauses

    def _axiom_A7(self, greaterH: Set[Tuple[int, int]]) -> List[Clause]:
        clauses = []
        for (i, j) in greaterH: 
            if j + 1 > self.N:
                continue
            for v1, v2 in iproduct(self.domain, repeat=2):
                if v1 <= v2:
                    clauses.append(frozenset([_GH(i, j,     True),
                                              _Val(i, j,   v1, True),
                                              _Val(i, j+1, v2, True)]))
        return clauses

    def _axiom_A8(self, lessV: Set[Tuple[int, int]]) -> List[Clause]:
        clauses = []
        for (i, j) in lessV:
            if i + 1 > self.N:
                continue
            for v1, v2 in iproduct(self.domain, repeat=2):
                if v1 >= v2:
                    clauses.append(frozenset([_LV(i, j,     True),
                                              _Val(i,   j, v1, True),
                                              _Val(i+1, j, v2, True)]))
        return clauses

    def _axiom_A9(self, greaterV: Set[Tuple[int, int]]) -> List[Clause]:
        clauses = []
        for (i, j) in greaterV:
            if i + 1 > self.N:
                continue
            for v1, v2 in iproduct(self.domain, repeat=2):
                if v1 <= v2:
                    clauses.append(frozenset([_GrV(i, j,     True),
                                              _Val(i,   j, v1, True),
                                              _Val(i+1, j, v2, True)]))
        return clauses

    def generate_full_ground_kb(
        self,
        futo=None,
        givens:   List[Tuple[int, int, int]] = None,
        lessH:    Set[Tuple[int, int]] = None,
        greaterH: Set[Tuple[int, int]] = None,
        lessV:    Set[Tuple[int, int]] = None,
        greaterV: Set[Tuple[int, int]] = None,
    ) -> GroundKB:
        if futo is not None:
            givens   = futo.get_givens()
            lessH    = futo.get_lessH_facts()
            greaterH = futo.get_greaterH_facts()
            lessV    = futo.get_lessV_facts()
            greaterV = futo.get_greaterV_facts()

        cell_clauses   = self._axiom_A1() + self._axiom_A2()
        unique_clauses = self._axiom_A3() + self._axiom_A4()
        ineq_clauses   = (self._axiom_A6(lessH)    +
                          self._axiom_A7(greaterH) +
                          self._axiom_A8(lessV)    +
                          self._axiom_A9(greaterV))
        given_clauses  = self._axiom_A5(givens)
        all_clauses    = cell_clauses + unique_clauses + ineq_clauses + given_clauses
        return GroundKB(
            cell_clauses   = cell_clauses,
            unique_clauses = unique_clauses,
            ineq_clauses   = ineq_clauses,
            given_clauses  = given_clauses,
            all_clauses    = all_clauses,
        )
    def populate_fc_engine(
        self, 
        engine, 
        givens: List[Tuple[int, int, int]],
        lessH: Set[Tuple[int, int]],
        greaterH: Set[Tuple[int, int]],
        lessV: Set[Tuple[int, int]],
        greaterV: Set[Tuple[int, int]]
    ):
        initial_facts = []
        for (i, j, v) in givens:
            initial_facts.append(f"Val_{i}_{j}_{v}")
        
        for (i, j) in lessH:    initial_facts.append(f"LessH_{i}_{j}")
        for (i, j) in greaterH: initial_facts.append(f"GreaterH_{i}_{j}")
        for (i, j) in lessV:    initial_facts.append(f"LessV_{i}_{j}")
        for (i, j) in greaterV: initial_facts.append(f"GreaterV_{i}_{j}")
        
        engine.add_initial_facts(initial_facts)

        for i, j in self.cells:
            for v in self.domain:
                premises = [f"Not_Val_{i}_{j}_{v_other}" for v_other in self.domain if v_other != v]
                conclusion = f"Val_{i}_{j}_{v}"
                engine.add_rule(premises, conclusion)

        for i, j in self.cells:
            for v in self.domain:
                for v_other in self.domain:
                    if v != v_other:
                        engine.add_rule([f"Val_{i}_{j}_{v}"], f"Not_Val_{i}_{j}_{v_other}")

        for i in self.domain:
            for v in self.domain:
                for j1 in self.domain:
                    for j2 in self.domain:
                        if j1 != j2:
                            engine.add_rule([f"Val_{i}_{j1}_{v}"], f"Not_Val_{i}_{j2}_{v}")

        for j in self.domain:
            for v in self.domain:
                for i1 in self.domain:
                    for i2 in self.domain:
                        if i1 != i2:
                            engine.add_rule([f"Val_{i1}_{j}_{v}"], f"Not_Val_{i2}_{j}_{v}")

        for (i, j) in lessH:
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 >= v2:
                        engine.add_rule([f"LessH_{i}_{j}", f"Val_{i}_{j}_{v1}"], f"Not_Val_{i}_{j+1}_{v2}")
                        engine.add_rule([f"LessH_{i}_{j}", f"Val_{i}_{j+1}_{v2}"], f"Not_Val_{i}_{j}_{v1}")

        for (i, j) in greaterH:
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 <= v2:
                        engine.add_rule([f"GreaterH_{i}_{j}", f"Val_{i}_{j}_{v1}"], f"Not_Val_{i}_{j+1}_{v2}")
                        engine.add_rule([f"GreaterH_{i}_{j}", f"Val_{i}_{j+1}_{v2}"], f"Not_Val_{i}_{j}_{v1}")

        for (i, j) in lessV:
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 >= v2:
                        engine.add_rule([f"LessV_{i}_{j}", f"Val_{i}_{j}_{v1}"], f"Not_Val_{i+1}_{j}_{v2}")
                        engine.add_rule([f"LessV_{i}_{j}", f"Val_{i+1}_{j}_{v2}"], f"Not_Val_{i}_{j}_{v1}")
        for (i, j) in greaterV:
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 <= v2:
                        engine.add_rule([f"GreaterV_{i}_{j}", f"Val_{i}_{j}_{v1}"], f"Not_Val_{i+1}_{j}_{v2}")
                        engine.add_rule([f"GreaterV_{i}_{j}", f"Val_{i+1}_{j}_{v2}"], f"Not_Val_{i}_{j}_{v1}")


def _clause_str(c: Clause) -> str:
    return " ∨ ".join(sorted(str(lit) for lit in c))

def print_ground_kb(kb: GroundKB) -> None:
    sep  = "=" * 70
    dash = "-" * 70
    print(sep)
    print("FULL GROUND KNOWLEDGE BASE  (CNF – Futoshiki)")
    print(sep)
    print("\n1. Cell Constraints (A1, A2):")
    print(dash)
    print("  [A1] Each cell holds at least one value:")
    seen_cells: set = set()
    for c in kb.cell_clauses:
        lits = list(c)
        if all(not lit.negated for lit in lits) and lits[0].pred == "Val":
            i, j = lits[0].args[0], lits[0].args[1]
            if (i, j) not in seen_cells:
                seen_cells.add((i, j))
                vals = " ∨ ".join(
                    f"Val({i},{j},{v})" for v in sorted(l.args[2] for l in lits)
                )
                print(f"    {vals}")
    print("  [A2] Each cell holds at most one value:")
    seen_a2: set = set()
    for c in kb.cell_clauses:
        lits = sorted(c, key=lambda l: l.args)
        if (len(lits) == 2
                and all(l.negated for l in lits)
                and lits[0].pred == "Val"
                and lits[0].args[:2] == lits[1].args[:2]):
            i, j = lits[0].args[0], lits[0].args[1]
            v1   = min(lits[0].args[2], lits[1].args[2])
            v2   = max(lits[0].args[2], lits[1].args[2])
            key  = (i, j, v1, v2)
            if key not in seen_a2:
                seen_a2.add(key)
                print(f"    ¬Val({i},{j},{v1}) ∨ ¬Val({i},{j},{v2})")
    print("\n2. Row & Column Uniqueness (A3, A4):")
    print(dash)
    seen_uniq: set = set()
    for c in kb.unique_clauses:
        lits = sorted(c, key=lambda l: l.args)
        if len(lits) != 2:
            continue
        (i1, j1, v1), (i2, j2, v2) = lits[0].args, lits[1].args
        if v1 != v2:
            continue
        v = v1
        if i1 == i2:
            key = ("A3", i1, v, min(j1, j2), max(j1, j2))
            if key not in seen_uniq:
                seen_uniq.add(key)
                print(f"  [A3] ¬Val({i1},{min(j1,j2)},{v}) ∨ ¬Val({i1},{max(j1,j2)},{v})")
        elif j1 == j2:
            key = ("A4", j1, v, min(i1, i2), max(i1, i2))
            if key not in seen_uniq:
                seen_uniq.add(key)
                print(f"  [A4] ¬Val({min(i1,i2)},{j1},{v}) ∨ ¬Val({max(i1,i2)},{j1},{v})")
    print("\n3. Inequality Rules (A6 – LessH, A7 – GreaterH, "
          "A8 – LessV, A9 – GreaterV):")
    print(dash)
    if kb.ineq_clauses:
        for c in kb.ineq_clauses:
            print(f"  {_clause_str(c)}")
    else:
        print("  (none – no inequality constraints in this puzzle)")
    print("\n4. Initial Facts (Given):")
    print(dash)
    if kb.given_clauses:
        for c in kb.given_clauses:
            print(f"  {_clause_str(c)}")
    else:
        print("  (no given clues)")
    print(f"\n  Total CNF clauses : {len(kb.all_clauses)}")
    print(sep)