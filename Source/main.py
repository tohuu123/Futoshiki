from Solver import Solver
from parser import parse_futoshiki
from KBgenerator import GroundKBGenerator, print_ground_kb

if __name__ == "__main__":
    inputfile  = "Inputs/input-01.txt"
    outputfile = "output-01.txt"
    futo = parse_futoshiki(inputfile)

    # ground KB gneration from FOL axioms
    gen = GroundKBGenerator(futo.N)
    kb  = gen.generate_full_ground_kb(futo)
    print_ground_kb(kb)

    # solve using different methods
    solver = Solver(futo)
    result = solver.compare_all(outputfile)
