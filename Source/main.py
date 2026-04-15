from KBgenerator import GroundKBGenerator
from BackwardChaining import build_futoshiki_engine, solve_futoshiki_with_backward_chaining
from parser import parse_futoshiki
from Bruteforce import *
from Backtracking import *
from Helper import print_output

if __name__ == "__main__": 
    inputfile = "Inputs/input-01.txt"
    outputfile = "output-01.txt"

    futo = parse_futoshiki(inputfile)
    lessH = futo.get_lessH_facts()
    greaterH = futo.get_greaterH_facts()
    lessV = futo.get_lessV_facts()
    greaterV = futo.get_greaterV_facts()
    givens = futo.get_givens()

    # TESTING Forward Chaining 
    kb = GroundKBGenerator(futo.N)
    kb.build(givens, lessH, greaterH, lessV, greaterV)
    fc_ok, inferred = kb.ForwardChainingEngine.run_inference()
    print("Forward Chaining solved:", fc_ok)
    print("Forward Chaining inferred facts:", len(inferred))

    # SOLVING with backward chaining guided search
    solved = solve_futoshiki_with_backward_chaining(futo)
    print("Solved by Backward Chaining:", solved)

    # Optional fallback solvers
    if not solved:
        solved = backtracking(futo)
        print("Solved by Backtracking fallback:", solved)

    if not solved:
        solved = brute_force(futo)
        print("Solved by Brute-force fallback:", solved)

    print_output(futo, outputfile)


