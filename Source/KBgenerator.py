from __future__ import annotations
from itertools import product as iproduct
from typing import List, Set, FrozenSet, Tuple
from ForwardChaining import ForwardChainingEngine
# Define Literal
class Literal():      
    def __init__(self, pred: str, args: Tuple, negated: bool = False):
        self.pred = pred
        self.args = args
        self.negated = negated
    def __neg__(self) -> "Literal":
        return Literal(self.pred, self.args, not self.negated)
    def __str__(self) -> str:
        sign = "¬" if self.negated else ""
        args = ",".join(map(str, self.args))
        return f"{sign}{self.pred}({args})"
    def atom(self) -> "Literal":
        """Return a positive literal"""
        return Literal(self.pred, self.args, False)
    
# Use frozenset avoid duplicates
# Clause include Literal

Clause = FrozenSet[Literal]

def clause(lits:List[Literal]) -> Clause: 
    return frozenset(lits)

def neg(lit: Literal) -> Literal: 
    return -lit

# Generate ground Knowledge base from FOL (AXIOMS A1 – A9)
def _Val(i, j, v, neg=False) -> Literal: return Literal("Val",(i,j,v), neg)

# haven's used yet
def _GV (i, j, v, neg = False) -> Literal: return Literal("Given", (i,j,v), neg)
def _LH (i, j, neg=False) -> Literal: return Literal("LessH", (i,j), neg)
def _GH (i, j, neg=False) -> Literal: return Literal("GreaterH",(i,j), neg)
def _LV (i, j, neg=False) -> Literal: return Literal("LessV", (i,j), neg)
def _GV (i, j, neg=False) -> Literal: return Literal("GreaterV",(i,j), neg)

class GroundKBGenerator:
    def __init__(self, N: int):
        self.N = N
        self.domain = list(range(1, N + 1))   
        self.cells  = [(i, j) for i in self.domain for j in self.domain]
        self._clauses: List[Clause] = [] # cnf
        # i use ForwardChaining engine first
        self.ForwardChainingEngine = ForwardChainingEngine()

    def _add_initial_facts(
        self,
        givens: List[Tuple[int, int, int]],
        lessH: Set[Tuple[int, int]],
        greaterH: Set[Tuple[int, int]],
        lessV: Set[Tuple[int, int]],
        greaterV: Set[Tuple[int, int]],
    ):
        facts = []

        for (i, j, v) in givens:
            facts.append(f"Val_{i}_{j}_{v}")

        for (i, j) in lessH:
            facts.append(f"LessH_{i}_{j}")

        for (i, j) in greaterH:
            facts.append(f"GreaterH_{i}_{j}")

        for (i, j) in lessV:
            facts.append(f"LessV_{i}_{j}")

        for (i, j) in greaterV:
            facts.append(f"GreaterV_{i}_{j}")

        self.ForwardChainingEngine.add_initial_facts(facts)
    # def _add(self, lits: List[Literal]):
    #     "Adding a clause"
    #     self._clauses.append(frozenset(lits))
    # Axiom A1-A9
    def _axiom_A1(self):
        for i, j in self.cells:
            for target in self.domain:
                 for v in self.domain: 
                    if (v != target): 
                        self.ForwardChainingEngine.add_rule(
                                premises=[f"Val_{i}_{j}_{target}"],
                                conclusion=f"Not_Val_{i}_{j}_{v}"
                    )
    def _axiom_A2(self):
        for i, j in self.cells:
            for v1 in self.domain: 
                for v2 in self.domain:  
                    if v1 < v2: # like v1 khac v2
                        # self._add([_Val(i, j, v1, neg=True), _Val(i, j, v2, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                            premises=[f"Val_{i}_{j}_{v1}"],
                            conclusion=f"Not_Val_{i}_{j}_{v2}"
                        )
    # Row uniqueness  
    def _axiom_A3(self):
        for i in self.domain:
            for v in self.domain:
                for j1, j2 in iproduct(self.domain, repeat=2):
                    if j1 < j2:
                        # self._add([_Val(i, j1, v, neg=True),
                        #           _Val(i, j2, v, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                                premises=[f"Val_{i}_{j1}_{v}"],
                                conclusion=f"Not_Val_{i}_{j2}_{v}"
                            )
    # Column uniqueness
    def _axiom_A4_col(self):
        for j in self.domain:
            for v in self.domain:
                for i1, i2 in iproduct(self.domain, repeat=2):
                    if i1 < i2:
                        # self._add([_Val(i1, j, v, neg=True),
                        #           _Val(i2, j, v, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                                premises=[f"Val_{i1}_{j}_{v}"],
                                conclusion=f"Not_Val_{i2}_{j}_{v}"
                            )
 
    # Given clues  
    def _axiom_A5_givens(self, givens: List[Tuple[int,int,int]]):
        for (i, j, v) in givens:
            # self._add(_Val(i, j, v))
            for v2 in self.domain:
                if v2 != v:
                    # self._add([_Val(i, j, v2, neg=True)])
                    self.ForwardChainingEngine.add_rule(
                                premises=[f"Val_{i}_{j}_{v}"],
                                conclusion=f"Not_Val_{i}_{j}_{v2}"
                    )
    # Horizontal less-than 
    def _axiom_A6_lessH(self, lessH_facts: Set[Tuple[int,int]]):
        for (i, j) in lessH_facts:
            if j + 1 > self.N:
                continue
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 >= v2:   # vi phạm v1 < v2
                        # self._add([_Val(i, j, v1, neg=True),
                        #           _Val(i, j+1, v2, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                            premises=[f"LessH_{i}_{j}", f"Val_{i}_{j}_{v1}"],
                            conclusion=f"Not_Val_{i}_{j+1}_{v2}"
                        )
 
    # Horizontal greater-than 
    def _axiom_A7_greaterH(self, greaterH_facts: Set[Tuple[int,int]]):
        for (i, j) in greaterH_facts:
            if j + 1 > self.N:
                continue
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 <= v2:   
                        # self._add([_Val(i, j,   v1, neg=True),
                        #           _Val(i, j+1, v2, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                            premises=[f"GreaterH_{i}_{j}", f"Val_{i}_{j}_{v1}"],
                            conclusion=f"Not_Val_{i}_{j+1}_{v2}"
                        )                        
 
    # Vertical less-than 
    def _axiom_A8_lessV(self, lessV_facts: Set[Tuple[int,int]]):
        for (i, j) in lessV_facts:
            if i + 1 > self.N:
                continue
            for v1 in self.domain:
                for v2 in self.domain:
                    if v1 >= v2:
                        # self._add([_Val(i, j, v1, neg=True),
                        #           _Val(i+1, j, v2, neg=True)])
                        self.ForwardChainingEngine.add_rule(
                            premises=[f"LessV_{i}_{j}", f"Val_{i}_{j}_{v1}"],
                            conclusion=f"Not_Val_{i+1}_{j}_{v2}"
                        )
    def _axiom_A9_greaterV(self, greaterV_facts: Set[Tuple[int,int]]):
        for (i, j) in greaterV_facts:
            if i + 1 > self.N:
                continue
            for v1 in self.domain:
                for v2 in self.domain:
                   if v1 <= v2:
                        # self._add([_Val(i,  j, v1, neg=True),
                        #           _Val(i+1, j, v2, neg=True)])
                        self.ForwardChainingEngine.add_rule (
                            premises=[f"GreaterV_{i}_{j}", f"Val_{i}_{j}_{v1}"],
                            conclusion=f"Not_Val_{i+1}_{j}_{v2}"
                        )
    def build(self, givens, lessH, greaterH, lessV, greaterV):
        self._add_initial_facts(givens, lessH, greaterH, lessV, greaterV)
        self._axiom_A1()
        self._axiom_A2()
        self._axiom_A3()
        self._axiom_A4_col()
        self._axiom_A5_givens(givens)
        self._axiom_A6_lessH(lessH)
        self._axiom_A7_greaterH(greaterH)
        self._axiom_A8_lessV(lessV)
        self._axiom_A9_greaterV(greaterV)   