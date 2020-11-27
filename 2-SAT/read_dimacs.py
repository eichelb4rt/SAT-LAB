#!/bin/python3
# SHEBANG

import argparse
from typing import List

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar = 'input',
        dest = 'input',
        type = str,
        help = 'Input file where DIMACS notation of a formular is stored.'
    )
    args = parser.parse_args()
    with open(args.input, "r") as f:
        print(read_cnf(f.readlines()))

def get_variables_in_dimacs(dimacs: List[str]) -> int:
    """Get the number of variables that are set in the DIMACS encoding.

    Parameters
    ----------
    dimacs : List[str]
        DIMACS encoded CNF. Pass it with file.readlines()

    Returns
    -------
    int
        Number of variables.
    """
    
    # determine where the problem starts
    start_index = 0
    for line_number, line in enumerate(dimacs):
        if line.startswith("p cnf"):
            start_index = line_number
            break
    
    # get n and c.
    try:
        problem_args = dimacs[start_index].replace('\n', '').split(' ')  # delete the line break and split it into args
        return int(problem_args[2])
        
    # if something goes wrong, it was probably not DIMACS encoded.
    except Exception:
        raise SyntaxError("This is not a DIMACS encoded formula.")

def read_cnf(dimacs: List[str]) -> List[List[int]]:
    """Reads a DIMACS encoded CNF.

    Parameters
    ----------
    dimacs : List[str]
        DIMACS encoded CNF. Pass it with file.readlines().

    Returns
    -------
    List[List[int]]
        The CNF.
    """

    # determine where the problem starts
    start_index = 0
    for line_number, line in enumerate(dimacs):
        if line.startswith("p cnf"):
            start_index = line_number
            break
    
    # get n and c.
    try:
        problem_args = dimacs[start_index].replace('\n', '').split(' ')  # delete the line break and split it into args
        n = int(problem_args[2])
        c = int(problem_args[3])
        
    # if something goes wrong, it was probably not DIMACS encoded.
    except Exception:
        raise SyntaxError("This is not a DIMACS encoded formula.")
    
    # build the cnf
    cnf = []
    for line_number, clause_dimacs in enumerate(dimacs[start_index+1:]):   # clauses come after the first line
        clause_dimacs = clause_dimacs.replace('\n', '') # delete line break
        clause = [int(literal) for literal in clause_dimacs.split(" ")] # get the literals seperated by space
        if clause[-1] == 0: # 0-terminated clauses
            cnf.append(clause[:-1]) # append the list without the terminating 0
        else:
            raise SyntaxError(f"No 0-terminated clause in line {line_number}")
    return cnf

if __name__ == "__main__":
    main()