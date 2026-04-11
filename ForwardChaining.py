from collections import deque, defaultdict 

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
    def add_rule(self, premises: list, conclusion: str):
        rule_id = len(self.ground_KB)
        self.ground_KB.append(Rule(rule_id, premises, conclusion))
        self.count[rule_id] = len(premises)
        for p in premises:
            self.premise_to_rules[p].append(rule_id)
    def add_initial_facts(self, facts: list):
        for fact in facts:
            self.agenda.append(fact)
    def run_inference(self):
        """Main Forward Chaining"""
        while self.agenda:
            p = self.agenda.popleft()
            if p not in self.inferred:
                self.inferred.add(p)
                # mapping
                for rule_id in self.premise_to_rules[p]:
                    self.count[rule_id] -= 1
                    if self.count[rule_id] == 0:
                        conclusion = self.ground_KB[rule_id].conclusion
                        self.agenda.append(conclusion)
        return self.inferred 