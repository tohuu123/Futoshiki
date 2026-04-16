from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Callable, Dict, Generator, Iterable, List, Optional, Sequence, Set, Tuple, Union


Term = Union["Variable", "Structure", int, str]
Substitution = Dict[str, Term]

@dataclass(frozen=True)
class Variable:
	name: str

	def __str__(self) -> str:
		return self.name

@dataclass(frozen=True)
class Structure:
	name: str
	args: Tuple[Term, ...]

	def __str__(self) -> str:
		if not self.args:
			return self.name
		rendered = ",".join(term_to_string(arg) for arg in self.args)
		return f"{self.name}({rendered})"


@dataclass(frozen=True)
class Clause:
	head: Structure
	body: Tuple[Structure, ...]


def is_variable(term: Term) -> bool:
	return isinstance(term, Variable)


def is_structure(term: Term) -> bool:
	return isinstance(term, Structure)


def term_to_string(term: Term) -> str:
	if isinstance(term, (Variable, Structure)):
		return str(term)
	return str(term)

def _split_top_level(text: str, sep: str = ",") -> List[str]:
	parts: List[str] = []
	depth = 0
	start = 0
	for idx, ch in enumerate(text):
		if ch == "(":
			depth += 1
		elif ch == ")":
			depth -= 1
			if depth < 0:
				raise ValueError(f"Unbalanced parentheses in: {text}")
		elif ch == sep and depth == 0:
			parts.append(text[start:idx].strip())
			start = idx + 1

	if depth != 0:
		raise ValueError(f"Unbalanced parentheses in: {text}")

	tail = text[start:].strip()
	if tail:
		parts.append(tail)
	return parts


def _parse_atom(token: str) -> Term:
	token = token.strip()
	if not token:
		raise ValueError("Empty token")

	if token.lstrip("-").isdigit():
		return int(token)

	if token[0].isupper() or token[0] == "_":
		return Variable(token)

	return token


def parse_term(text: str) -> Structure:
	text = text.strip()
	if text.endswith("?") or text.endswith("."):
		text = text[:-1].strip()

	if "(" not in text:
		atom = _parse_atom(text)
		if not isinstance(atom, Structure):
			if isinstance(atom, Variable):
				raise ValueError(f"Predicate cannot be a standalone variable: {text}")
			return Structure(str(atom), tuple())

	left = text.find("(")
	if left == -1 or not text.endswith(")"):
		raise ValueError(f"Invalid term format: {text}")

	name = text[:left].strip()
	inside = text[left + 1 : -1].strip()
	if not name:
		raise ValueError(f"Missing predicate name: {text}")

	if not inside:
		return Structure(name, tuple())

	args: List[Term] = []
	for token in _split_top_level(inside, ","):
		token = token.strip()
		if "(" in token:
			args.append(parse_term(token))
		else:
			args.append(_parse_atom(token))

	return Structure(name, tuple(args))


def parse_clause(text: str) -> Clause:
	text = text.strip()
	if text.endswith("."):
		text = text[:-1].strip()

	if ":-" not in text:
		return Clause(parse_term(text), tuple())

	head_s, body_s = text.split(":-", 1)
	head = parse_term(head_s.strip())
	body_tokens = _split_top_level(body_s.strip(), ",")
	body = tuple(parse_term(token.strip()) for token in body_tokens if token.strip())
	return Clause(head, body)


def walk(term: Term, theta: Substitution) -> Term:
	while isinstance(term, Variable) and term.name in theta:
		replacement = theta[term.name]
		if replacement == term:
			break
		term = replacement
	return term


def apply_substitution(term: Union[Term, Sequence[Structure]], theta: Substitution):
	if isinstance(term, list):
		return [apply_substitution(item, theta) for item in term]
	if isinstance(term, tuple):
		return tuple(apply_substitution(item, theta) for item in term)
	if isinstance(term, Variable):
		resolved = walk(term, theta)
		if isinstance(resolved, Variable):
			return resolved
		return apply_substitution(resolved, theta)
	if isinstance(term, Structure):
		return Structure(term.name, tuple(apply_substitution(arg, theta) for arg in term.args))
	return term


def _occurs_check(var: Variable, term: Term, theta: Substitution) -> bool:
	term = apply_substitution(term, theta)
	if var == term:
		return True
	if isinstance(term, Structure):
		return any(_occurs_check(var, arg, theta) for arg in term.args)
	return False


def _unify_var(var: Variable, x: Term, theta: Substitution) -> Optional[Substitution]:
	x = apply_substitution(x, theta)
	existing = theta.get(var.name)

	if existing is not None:
		return unify(existing, x, theta)

	if isinstance(x, Variable):
		x_existing = theta.get(x.name)
		if x_existing is not None:
			return unify(var, x_existing, theta)

	if _occurs_check(var, x, theta):
		return None

	next_theta = dict(theta)
	next_theta[var.name] = x
	return next_theta


def unify(x: Term, y: Term, theta: Optional[Substitution] = None) -> Optional[Substitution]:
	if theta is None:
		theta = {}

	x = apply_substitution(x, theta)
	y = apply_substitution(y, theta)

	if x == y:
		return dict(theta)

	if isinstance(x, Variable):
		return _unify_var(x, y, theta)
	if isinstance(y, Variable):
		return _unify_var(y, x, theta)

	if isinstance(x, Structure) and isinstance(y, Structure):
		if x.name != y.name or len(x.args) != len(y.args):
			return None

		current = dict(theta)
		for xa, ya in zip(x.args, y.args):
			current = unify(xa, ya, current)
			if current is None:
				return None
		return current

	return None


def _collect_variables(term: Union[Term, Clause], collector: Dict[str, Variable]) -> None:
	if isinstance(term, Variable):
		collector[term.name] = term
		return
	if isinstance(term, Structure):
		for arg in term.args:
			_collect_variables(arg, collector)
		return
	if isinstance(term, Clause):
		_collect_variables(term.head, collector)
		for goal in term.body:
			_collect_variables(goal, collector)


_rename_counter = count(1)


def rename_apart(clause: Clause) -> Clause:
	var_map: Dict[str, Variable] = {}
	found: Dict[str, Variable] = {}
	_collect_variables(clause, found)
	suffix = next(_rename_counter)

	for original in found:
		var_map[original] = Variable(f"{original}_{suffix}")

	theta: Substitution = {name: mapped for name, mapped in var_map.items()}
	head = apply_substitution(clause.head, theta)
	body = tuple(apply_substitution(goal, theta) for goal in clause.body)
	return Clause(head=head, body=body)


def _term_to_python(term: Term):
	resolved = term
	if isinstance(resolved, Variable):
		return resolved.name
	if isinstance(resolved, Structure):
		return term_to_string(resolved)
	return resolved


class BackwardChainingEngine:
	def __init__(
		self,
		clauses: Optional[Iterable[Clause]] = None,
		max_depth: int = 120,
	):
		self.clauses: List[Clause] = list(clauses or [])
		self.max_depth = max_depth
		self.builtins: Dict[str, Callable[[Structure, Substitution], List[Substitution]]] = {
			"Diff": self._builtin_diff,
			"Neq": self._builtin_diff,
			"Eq": self._builtin_eq,
			"Less": self._builtin_less,
			"Greater": self._builtin_greater,
			"SameRow": self._builtin_same_row,
			"SameCol": self._builtin_same_col,
		}
		self.futoshiki_context: Dict[str, object] = {}

	def add_clause(self, clause: Union[Clause, str]) -> None:
		if isinstance(clause, str):
			clause = parse_clause(clause)
		self.clauses.append(clause)

	def add_fact(self, fact: Union[Structure, str]) -> None:
		if isinstance(fact, str):
			fact = parse_term(fact)
		self.clauses.append(Clause(head=fact, body=tuple()))

	def is_fact(self, goal: Union[Structure, str], theta: Optional[Substitution] = None) -> bool:
		if isinstance(goal, str):
			goal = parse_term(goal)
		base_theta = theta or {}

		for clause in self.clauses:
			if clause.body:
				continue
			renamed = rename_apart(clause)
			if unify(goal, renamed.head, base_theta) is not None:
				return True
		return False

	def is_builtin(self, goal: Union[Structure, str]) -> bool:
		if isinstance(goal, str):
			goal = parse_term(goal)
		return goal.name in self.builtins

	def ask(self, goal: Union[Structure, str]) -> bool:
		return len(self.query(goal)) > 0

	def query(self, goal: Union[Structure, str]) -> List[Dict[str, object]]:
		if isinstance(goal, str):
			goal = parse_term(goal)

		query_vars = self._vars_of(goal)
		answers: List[Dict[str, object]] = []

		for theta in self.sld_resolve([goal], {}):
			answer: Dict[str, object] = {}
			for var_name in query_vars:
				value = apply_substitution(Variable(var_name), theta)
				answer[var_name] = _term_to_python(value)
			answers.append(answer)

		return answers

	def query_cell(self, i: int, j: int, verbose: bool = True) -> List[int]:
		if verbose:
			print(f"Querying cell ({i}, {j}) → Val({i}, {j}, V)?")
		answers = self.query(Structure("Val", (i, j, Variable("V"))))
		values: Set[int] = set()
		for answer in answers:
			value = answer.get("V")
			if isinstance(value, int):
				values.add(value)
		result = sorted(values)
		if verbose:
			if result:
				print(f"Cell ({i}, {j}) candidates: {result}")
			else:
				print(f"Cell ({i}, {j}) → no valid candidates found")
		return result

	def sld_resolve(
		self,
		goals: List[Structure],
		theta: Substitution,
		depth: int = 0,
		visited: Optional[Set[Tuple[str, ...]]] = None,
	) -> Generator[Substitution, None, None]:
		if visited is None:
			visited = set()

		applied_goals = [apply_substitution(goal, theta) for goal in goals]

		if not applied_goals:
			yield theta
			return

		if depth > self.max_depth:
			return

		state_key = tuple(term_to_string(g) for g in applied_goals)
		if state_key in visited:
			return

		branch_visited = set(visited)
		branch_visited.add(state_key)

		goal = applied_goals[0]
		rest_goals = applied_goals[1:]

		if self.is_builtin(goal):
			for next_theta in self._run_builtin(goal, theta):
				yield from self.sld_resolve(rest_goals, next_theta, depth + 1, branch_visited)
			return

		for clause in self.clauses:
			renamed = rename_apart(clause)
			theta1 = unify(goal, renamed.head, theta)
			if theta1 is None:
				continue

			new_goals = list(renamed.body) + rest_goals
			new_goals = [apply_substitution(g, theta1) for g in new_goals]
			yield from self.sld_resolve(new_goals, theta1, depth + 1, branch_visited)

	def _vars_of(self, term: Term) -> List[str]:
		found: Dict[str, Variable] = {}
		_collect_variables(term, found)
		return sorted(found.keys())

	def _run_builtin(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		fn = self.builtins.get(goal.name)
		if fn is None:
			return []
		return fn(goal, theta)

	def _require_ground(self, term: Term, theta: Substitution):
		value = apply_substitution(term, theta)
		if isinstance(value, Variable):
			return None
		return value

	def _builtin_eq(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 2:
			return []
		merged = unify(goal.args[0], goal.args[1], theta)
		return [merged] if merged is not None else []

	def _builtin_diff(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 2:
			return []

		left = self._require_ground(goal.args[0], theta)
		right = self._require_ground(goal.args[1], theta)
		if left is None or right is None:
			return []
		return [theta] if left != right else []

	def _builtin_less(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 2:
			return []
		left = self._require_ground(goal.args[0], theta)
		right = self._require_ground(goal.args[1], theta)
		if not isinstance(left, int) or not isinstance(right, int):
			return []
		return [theta] if left < right else []

	def _builtin_greater(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 2:
			return []
		left = self._require_ground(goal.args[0], theta)
		right = self._require_ground(goal.args[1], theta)
		if not isinstance(left, int) or not isinstance(right, int):
			return []
		return [theta] if left > right else []

	def _builtin_same_row(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 4:
			return []
		i1 = self._require_ground(goal.args[0], theta)
		j1 = self._require_ground(goal.args[1], theta)
		i2 = self._require_ground(goal.args[2], theta)
		j2 = self._require_ground(goal.args[3], theta)
		if None in (i1, j1, i2, j2):
			return []
		return [theta] if (i1 == i2 and j1 != j2) else []

	def _builtin_same_col(self, goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 4:
			return []
		i1 = self._require_ground(goal.args[0], theta)
		j1 = self._require_ground(goal.args[1], theta)
		i2 = self._require_ground(goal.args[2], theta)
		j2 = self._require_ground(goal.args[3], theta)
		if None in (i1, j1, i2, j2):
			return []
		return [theta] if (j1 == j2 and i1 != i2) else []


def build_futoshiki_engine(
	n: int,
	givens: Sequence[Tuple[int, int, int]],
	less_h: Sequence[Tuple[int, int]],
	greater_h: Sequence[Tuple[int, int]],
	less_v: Sequence[Tuple[int, int]],
	greater_v: Sequence[Tuple[int, int]],
) -> BackwardChainingEngine:
	engine = BackwardChainingEngine()

	for i in range(1, n + 1):
		for j in range(1, n + 1):
			engine.add_fact(Structure("Cell", (i, j)))

	for v in range(1, n + 1):
		engine.add_fact(Structure("Domain", (v,)))

	for i, j, v in givens:
		engine.add_fact(Structure("Given", (i, j, v)))

	for i, j in less_h:
		engine.add_fact(Structure("LessH", (i, j)))
	for i, j in greater_h:
		engine.add_fact(Structure("GreaterH", (i, j)))
	for i, j in less_v:
		engine.add_fact(Structure("LessV", (i, j)))
	for i, j in greater_v:
		engine.add_fact(Structure("GreaterV", (i, j)))

	engine.add_clause("Val(I,J,V) :- Given(I,J,V).")
	engine.add_clause("Val(I,J,V) :- Cell(I,J), Domain(V), EmptyCell(I,J), Candidate(I,J,V).")
	engine.add_clause("NotVal(I,J,V2) :- Val(I,J,V1), Diff(V1,V2).")

	given_map: Dict[Tuple[int, int], int] = {(i, j): v for i, j, v in givens}
	less_h_set = set(less_h)
	greater_h_set = set(greater_h)
	less_v_set = set(less_v)
	greater_v_set = set(greater_v)

	def _neighbor_value(cell_i: int, cell_j: int) -> Optional[int]:
		return given_map.get((cell_i, cell_j))

	def builtin_empty_cell(goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 2:
			return []
		i_term = apply_substitution(goal.args[0], theta)
		j_term = apply_substitution(goal.args[1], theta)
		if not isinstance(i_term, int) or not isinstance(j_term, int):
			return []
		return [theta] if (i_term, j_term) not in given_map else []

	def builtin_candidate(goal: Structure, theta: Substitution) -> List[Substitution]:
		if len(goal.args) != 3:
			return []

		i_term = apply_substitution(goal.args[0], theta)
		j_term = apply_substitution(goal.args[1], theta)
		v_term = apply_substitution(goal.args[2], theta)

		if not isinstance(i_term, int) or not isinstance(j_term, int) or not isinstance(v_term, int):
			return []

		for (ri, rj), rv in given_map.items():
			if ri == i_term and rj != j_term and rv == v_term:
				return []
			if rj == j_term and ri != i_term and rv == v_term:
				return []

		if (i_term, j_term) in less_h_set:
			right = _neighbor_value(i_term, j_term + 1)
			if right is not None and not (v_term < right):
				return []
		if (i_term, j_term) in greater_h_set:
			right = _neighbor_value(i_term, j_term + 1)
			if right is not None and not (v_term > right):
				return []

		if (i_term, j_term - 1) in less_h_set:
			left = _neighbor_value(i_term, j_term - 1)
			if left is not None and not (left < v_term):
				return []
		if (i_term, j_term - 1) in greater_h_set:
			left = _neighbor_value(i_term, j_term - 1)
			if left is not None and not (left > v_term):
				return []

		if (i_term, j_term) in less_v_set:
			down = _neighbor_value(i_term + 1, j_term)
			if down is not None and not (v_term < down):
				return []
		if (i_term, j_term) in greater_v_set:
			down = _neighbor_value(i_term + 1, j_term)
			if down is not None and not (v_term > down):
				return []

		if (i_term - 1, j_term) in less_v_set:
			up = _neighbor_value(i_term - 1, j_term)
			if up is not None and not (up < v_term):
				return []
		if (i_term - 1, j_term) in greater_v_set:
			up = _neighbor_value(i_term - 1, j_term)
			if up is not None and not (up > v_term):
				return []

		return [theta]

	engine.builtins["EmptyCell"] = builtin_empty_cell
	engine.builtins["Candidate"] = builtin_candidate
	return engine


Parse_term = parse_term
Unify = unify
Apply_substitution = apply_substitution
Rename_apart = rename_apart
Sld_resolve = BackwardChainingEngine.sld_resolve
Ask = BackwardChainingEngine.ask
Query = BackwardChainingEngine.query
Query_cell = BackwardChainingEngine.query_cell
Is_fact = BackwardChainingEngine.is_fact
Is_builtin = BackwardChainingEngine.is_builtin


def solve_futoshiki_with_backward_chaining(futo) -> bool:
	"""Solve a Futoshiki grid using backward-chaining guided domains and DFS."""
	from Helper import is_valid

	def _find_mrv_cell_and_candidates():
		givens = futo.get_givens()
		engine = build_futoshiki_engine(
			futo.N,
			givens,
			futo.get_lessH_facts(),
			futo.get_greaterH_facts(),
			futo.get_lessV_facts(),
			futo.get_greaterV_facts(),
		)

		best_cell = None
		best_candidates: Optional[List[int]] = None

		for i in range(futo.N):
			for j in range(futo.N):
				if futo.grid[i][j] != 0:
					continue

				candidates = engine.query_cell(i + 1, j + 1)
				if not candidates:
					return (i, j), []

				if best_candidates is None or len(candidates) < len(best_candidates):
					best_cell = (i, j)
					best_candidates = candidates

		if best_cell is None:
			return None, []

		return best_cell, best_candidates or []

	def _dfs() -> bool:
		cell, candidates = _find_mrv_cell_and_candidates()
		if cell is None:
			return is_valid(futo, full_check=True)

		row, col = cell
		if not candidates:
			return False

		for value in candidates:
			futo.grid[row][col] = value
			if is_valid(futo, full_check=False) and _dfs():
				return True
			futo.grid[row][col] = 0

		return False

	return _dfs()
