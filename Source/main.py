from KBgenerator import GroundKBGenerator
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
    print(kb.ForwardChainingEngine.run_inference())

    # TESTING brute_force and backtracking
    brute_force(futo)
    # backtracking(futo)
    print_output(futo, outputfile)


