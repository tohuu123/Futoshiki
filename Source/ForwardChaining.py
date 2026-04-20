from collections import deque, defaultdict 
from KBgenerator import *

class Rule:
    def __init__(self, rule_id: int, premises: list, conclusion: str):
        self.rule_id = rule_id
        self.premises = premises      # Left (literals)
        self.conclusion = conclusion  # Right (Conclusion): Left => Right

class ForwardChainingEngine:
    def __init__(self):
        self.ground_KB = []
        self.count = {}                              
        self.premise_to_rules = defaultdict(list)  
        self.inferred = set()                       
        self.agenda = deque()
        self.conflicts = []
        self.empty_domain_cells = []

    def _complement(self, fact: str) -> str:
        if fact.startswith("Not_"):
            return fact[4:]
        return f"Not_{fact}"

    def _record_conflict(self, fact: str):
        opposite = self._complement(fact)
        if opposite in self.inferred:
            pair = tuple(sorted((fact, opposite)))
            if pair not in self.conflicts:
                self.conflicts.append(pair)

    def _parse_val_fact(self, fact: str):
        negated = False
        raw = fact
        if raw.startswith("Not_"):
            negated = True
            raw = raw[4:]

        parts = raw.split("_")
        if len(parts) != 4 or parts[0] != "Val":
            return None

        try:
            i = int(parts[1])
            j = int(parts[2])
            v = int(parts[3])
        except ValueError:
            return None

        return (i, j, v, negated)

    def _collect_cell_domains(self):
        domain_by_cell = defaultdict(set)
        negated_by_cell = defaultdict(set)

        for fact in self.inferred:
            parsed = self._parse_val_fact(fact)
            if parsed is None:
                continue
            i, j, v, negated = parsed
            key = (i, j)
            domain_by_cell[key].add(v)
            if negated:
                negated_by_cell[key].add(v)

        for rule in self.ground_KB:
            parsed_conclusion = self._parse_val_fact(rule.conclusion)
            if parsed_conclusion is not None:
                i, j, v, _ = parsed_conclusion
                domain_by_cell[(i, j)].add(v)

            for premise in rule.premises:
                parsed_premise = self._parse_val_fact(premise)
                if parsed_premise is None:
                    continue
                i, j, v, _ = parsed_premise
                domain_by_cell[(i, j)].add(v)

        return domain_by_cell, negated_by_cell

    def add_rule(self, premises: list, conclusion: str):
        rule_id = len(self.ground_KB)
        self.ground_KB.append(Rule(rule_id, premises, conclusion))
        self.count[rule_id] = len(premises)
        for p in premises:
            self.premise_to_rules[p].append(rule_id)

    def add_initial_facts(self, facts: list):
        for fact in facts:
            self.agenda.append(fact)

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def has_empty_domain(self) -> bool:
        domain_by_cell, negated_by_cell = self._collect_cell_domains()
        self.empty_domain_cells = []

        for cell, domain_values in domain_by_cell.items():
            if domain_values and domain_values.issubset(negated_by_cell[cell]):
                self.empty_domain_cells.append(cell)

        return len(self.empty_domain_cells) > 0

    def _print_detected_issues(self):
        if self.conflicts:
            print("Detected logical conflicts:")
            for left, right in self.conflicts:
                print(f"  - {left} <-> {right}")

        if self.empty_domain_cells:
            cells = ", ".join(f"({i},{j})" for i, j in sorted(self.empty_domain_cells))
            print(f"Detected empty domain at cells: {cells}")

    def run_inference(self, stop_on_conflict: bool = False):
        """Forward Chaining"""
        self.conflicts = []
        self.empty_domain_cells = []
        self.count = {rule.rule_id: len(rule.premises) for rule in self.ground_KB}

        while self.agenda:
            p = self.agenda.popleft()
            if p in self.inferred:
                 continue
            self._record_conflict(p)
            
            if stop_on_conflict:
                if self.has_conflicts() or self.has_empty_domain():
                    self._print_detected_issues()
                    return (False, self.inferred)
            
            self.inferred.add(p)
            # mapping
            for rule_id in self.premise_to_rules[p]:
                self.count[rule_id] -= 1
                if self.count[rule_id] == 0:
                    conclusion = self.ground_KB[rule_id].conclusion
                    self._record_conflict(conclusion)
                    if stop_on_conflict and self.has_conflicts():
                        self._print_detected_issues()
                        return (not self.has_conflicts(), self.inferred)
                    self.agenda.append(conclusion)
        final_conflict = self.has_conflicts() or self.has_empty_domain()
        if final_conflict:
            self._print_detected_issues()
        return (not final_conflict, self.inferred)

def solve_futoshiki_forward_chaining(futo):
    N        = futo.N
    givens   = futo.get_givens()
    lessH    = futo.get_lessH_facts()
    greaterH = futo.get_greaterH_facts()
    lessV    = futo.get_lessV_facts()
    greaterV = futo.get_greaterV_facts()

    gen = GroundKBGenerator(N)
    fc_engine = ForwardChainingEngine()

    gen.populate_fc_engine(
        engine=fc_engine,
        givens=givens,
        lessH=lessH,
        greaterH=greaterH,
        lessV=lessV,
        greaterV=greaterV
    )

    success, inferred_facts = fc_engine.run_inference(stop_on_conflict=True)
    return success, inferred_facts