#!/bin/python3
# SHEBANG

import os, sys, argparse
from copy import deepcopy

# add the 2-SAT directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/2-SAT")
import read_dimacs as dimacs    # no vscode, you're wrong. This is not an unresolved import. fucker.
from two_sat import unit_propagation, empty_set_contained, get_var, apply_assignment

# global variables
assignments = []
original_formula = []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar = 'input',
        dest = 'input',
        type = str,
        help = 'Input file where DIMACS notation of a formula is stored.'
    )
    parser.add_argument(
        '--show-assignments',
        dest = 'show_assignments',
        action = 'store_true',
        default = False,
        help = 'Show the assignments if it is satisfiable.'
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
    with open(args.input, "r") as new_f:
        formula = dimacs.read_cnf(new_f.readlines())
    global original_formula, local_formula
    original_formula = formula
    local_formula = formula

def dpll_mf() -> bool: # memory friendly
    global assignments, original_formula
    # unit propagation
    local_formula, new_assignments = unit_propagation(local_formula)
    assignments.append(new_assignments)
    # eliminate pure literals
    eliminate_pure_literals_mf()
    # set the entry point for backtracking here so we don't have to do the above repeatedly
    entry_point = len(assignments)  # entry point is the next index to be assigned
    # check for TERMINATION
    if is_empty_formula(local_formula):
        return True
    if empty_set_contained(local_formula):
        return False
    # Oh i'd like some sweet variables now. Wanna go buy some?
    decision_variable = get_var(local_formula)

def dpll() -> bool: # time friendly
    global assignments, original_formula
    local_formula = apply_assignments(original_formula, assignments)
    # unit propagation
    local_formula, new_assignments = unit_propagation(local_formula)
    assignments.append(new_assignments)
    # eliminate pure literals
    local_formula, new_assignments = eliminate_pure_literals(local_formula)
    assignments.append(new_assignments)
    # set the entry point for backtracking here so we don't have to do the above repeatedly
    entry_point = len(assignments)  # entry point is the next index to be assigned
    # check for TERMINATION
    if is_empty_formula(local_formula):
        return True
    if empty_set_contained(local_formula):
        return False
    # Oh i'd like some sweet variables now. Wanna go buy some?
    decision_variable = get_var(local_formula)

def unit_propagation_mf():
    """Applies unit propagation and adds the assigned assignments to the global list of assignments.
    """

    local_formula = apply_assignments(original_formula, assignments)
    new_assignments = unit_propagation(local_formula)[1]
    assignment.append(new_assignments)

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

def eliminate_pure_literals_mf(): # mf = memory friendly, obviously
    """Adds the assignments for pure literal elimination to the global list of assignments.
    """

    # get current formula
    global assignments
    local_formula = apply_assignments(original_formula, assignments)
    # get assignments for elimination
    for literal in get_pure_literals(local_formula):
        var = abs(literal)
        assigned_value = True if literal > 0 else False
        assignments.append((var, assigned_value))

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