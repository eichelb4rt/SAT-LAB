#!/bin/python3
# SHEBANG

import os, sys, argparse
from copy import deepcopy
from typing import List, Tuple, Optional

# add the 2-SAT directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}2-SAT")
import read_dimacs as dimacs    # no vscode, you're wrong. This is not an unresolved import. fucker.
from two_sat import unit_propagation, empty_set_contained, get_var, apply_assignment
from stats import DPLLStats, StatsAgent

# global variables
STATS = DPLLStats()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar = 'input',
        dest = 'input',
        type = str,
        help = 'Input file where DIMACS notation of a formula is stored.'
    )
    parser.add_argument(
        '-s',
        '--stats',
        dest = 'show_stats',
        action = 'store_true',
        default = False,
        help = 'Show the stats (memory usage, time).'
    )
    args = parser.parse_args()
    
    global STATS
    # solve the thing
    satisfiable = solve_input(args.input)
    # print results
    if satisfiable:
        print("Satisfiable")
    else:
        print("Unsatisfiable")
    # print stats
    if args.show_stats:
        print(STATS)

def solve_input(input: str) -> bool:
    """Solves SAT for a given input file with a CNF in dimacs and measures stats.

    Parameters
    ----------
    input : str
        The dimacs encoded file.

    Returns
    -------
    bool
        True if formula is satisfiable, False otherwise.
    """

    global STATS
    
    with open(input, "r") as f:
        formula = dimacs.read_cnf(f.readlines())
    # solve and measure stuff
    STATS.start()
    # now finally do the thing
    satisfiable = dpll(formula)
    # stop measuring of stats
    STATS.stop()
    return satisfiable
    

def dpll(f: List[List[int]]) -> bool:
    global STATS
    # unit propagation
    f, _ = unit_propagation(f, STATS)
    # eliminate pure literals
    f, _ = eliminate_pure_literals(f)
    # check for TERMINATION
    if is_empty_formula(f):
        return True
    if empty_set_contained(f):
        return False
    # Oh i'd like some sweet variables now. Wanna go buy some?
    decision_variable = get_var(f)
    STATS.decide()
    return dpll(apply_assignment(f, (decision_variable, True))) or dpll(apply_assignment(f, (decision_variable, False)))

def apply_assignments(f: List[List[int]], assignments: List[Tuple[int, bool]]) -> List[List[int]]:
    """Applies a list of assignments to a given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula f.
    assignments : List[Tuple[int, bool]]
        The list of assignments.

    Returns
    -------
    List[List[int]]
        The formula f with all the assignments applied.
    """

    for assignment in assignments:
        f = apply_assignment(f, assignment) # apply_assignments uses deep copies
    return f

def is_empty_formula(f: List[List[int]]) -> bool:
    """Determines whether a formula f is empty.

    Parameters
    ----------
    f : List[List[int]]
        The given formula f.

    Returns
    -------
    bool
        True if empty, False if not.
    """

    return len(f) == 0

def eliminate_pure_literals(f: List[List[int]]) -> Tuple[List[List[int]], List[Tuple[int, bool]]]:
    """Eliminates pure literals.

    Parameters
    ----------
    f : List[List[int]]
        The given formula f.

    Returns
    -------
    Tuple[List[List[int]], List[Tuple[int, bool]]]
        The formula with pure literals eliminated and the assignments that were assigned.
    """

    # get the pure literals
    pure_literals = get_pure_literals(f)

    # define the assignments
    assignments = []    # ! not the global assignments
    for literal in pure_literals:
        var = abs(literal)
        assigned_value = True if literal > 0 else False
        assignments.append((var, assigned_value))
    
    # determine the clauses that are to be eliminated
    eliminated_clauses = []
    for clause in f:
        for literal in clause:
            if literal in pure_literals:
                eliminated_clauses.append(clause)
    
    # ELIMINATE THEM
    f = [clause for clause in f if not clause in eliminated_clauses]
    return f, assignments

def get_pure_literals(f: List[List[int]]) -> List[int]:
    """Gets all the pure literal in a given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula f.

    Returns
    -------
    int
        All the pure literals. Empty list if none were found.
    """

    # first make a list of all the literals
    literals = []

    for clause in f:
        for literal in clause:
            if not literal in literals:
                literals.append(literal)
    
    # now return a list of all the pure literals (a literal is in the list below if it is in the literals list, but it's negated part is not)
    return [literal for literal in literals if not -literal in literals]

if __name__ == "__main__":
    main()