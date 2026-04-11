from KBgenerator import GroundKBGenerator
from parser import parse_futoshiki

if __name__ == "__main__":
    data = parse_futoshiki("Source/Inputs/input-01.txt")
    lessH = data.get_lessH_facts()
    
    greaterH = data.get_greaterH_facts()
    lessV = data.get_lessV_facts()
    greaterV = data.get_greaterV_facts()
    givens = data.get_givens()

    kb = GroundKBGenerator(data.N)
    kb.build(givens, lessH, greaterH, lessV, greaterV)
    print(kb.engine.run_inference())
