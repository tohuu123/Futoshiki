from Source.KBgenerator import GroundKBGenerator
from parser import parse_futoshiki
from Source.Brute_force import *

if __name__ == "__main__": 
    futo = parse_futoshiki("Inputs/input-02.txt")
    lessH = futo.get_lessH_facts()
    
    greaterH = futo.get_greaterH_facts()
    lessV = futo.get_lessV_facts()
    greaterV = futo.get_greaterV_facts()
    givens = futo.get_givens()

    kb = GroundKBGenerator(futo.N)
    kb.build(givens, lessH, greaterH, lessV, greaterV)
    print(kb.ForwardChainingEngine.run_inference())

    brute_force(futo)
    print_output(futo, "output-02.txt")


