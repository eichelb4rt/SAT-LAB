#!/bin/python3
# SHEBANG

import os, sys, argparse
from copy import deepcopy, copy
from typing import List, Tuple, Optional

# add the 2-SAT directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}2-SAT")
import read_dimacs as dimacs    # no vscode, you're wrong. This is not an unresolved import. fucker.
from two_sat import unit_propagation, apply_assignment

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
    with open(args.input, "r") as f:
        formula = dimacs.read_cnf(f.readlines())
    global original_formula, assignments
    original_formula = formula
    print(dpll_solver(), assignments)

def dpll_solver() -> bool:
    """DPLL with preprocessing.

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """

    # pre-processing
    # check for TERMINATION
    if is_empty_formula_mf():
        return True
    if empty_set_contained_mf():
        return False
    # the real thing
    return dpll_mf()

def dpll_mf() -> bool: # mf = memory friendly, obviously
    """The loop inside DPLL.

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """
    global assignments, original_formula    # we're using these global variables
    unit_propagation_mf()   # unit propagation
    eliminate_pure_literals_mf()    # eliminate pure literals
    # check for TERMINATION
    if is_empty_formula_mf():
        return True
    if empty_set_contained_mf():
        return False
    
    var = get_var_mf()  # Oh i'd like some sweet variables now. Wanna go get some?
    # recursion go brr
    entry_point = len(assignments)  # entry point is the index of the next variable to be assigned
    assignments.append((var, False))    # assign(var, 0)
    if dpll_mf():
        return True
    assignments = assignments[:entry_point] # unassign(x)
    # ite, let's just try it again, shall we?
    assignments.append((var, True))    # assign(var, 1)
    if dpll_mf():
        return True
    assignments = assignments[:entry_point] # unassign(x)
    return False

def get_var_mf() -> Optional[int]: # mf = memory friendly, obviously
    """Gets a variable from the formula.

    Returns
    -------
    Optional[int]
        Returns a variable from the formula, None if none was found.
    """

    global original_formula, assignments
    # get all the variables in the original formula
    variables = []
    for clause in original_formula:
        for literal in clause:
            var = abs(literal)
            if not var in variables:
                variables.append(var)
    # substract the ones that were already assigned
    assigned_vars = [var for (var, assigned_value) in assignments]
    variables = [var for var in variables if not var in assigned_vars]
    # skinny little boy, hasn't even got variables in him
    if len(variables) == 0:
        return None
    return variables[0]

def unit_propagation_mf():  # mf = memory friendly, obviously
    """Applies unit propagation and adds the assigned assignments to the global list of assignments.
    """

    global original_formula, assignments    # gonna use em both like every time
    local_formula = apply_assignments(original_formula, assignments)    # apply assignments (uses a deep copy)
    new_assignments = unit_propagation(local_formula)[1]    # do UP on the local formula
    for new_assignment in new_assignments:  # append the assignments assigned in UP
        assignments.append(new_assignment)

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

    # no deep copy needed (because apply_assignments already uses them)
    for assignment in assignments:
        f = apply_assignment(f, assignment) # apply_assignments uses deep copies
    return f

def empty_set_contained_mf() -> bool:   # mf = memory friendly, obviously
    """Determines whether the formula with the applied assignment contains an empty clause.

    Returns
    -------
    bool
        True if empty set is found.
    """

    global original_formula, assignments
    # idea: return true if any of the original clauses are a subset of the falsified literals
    falsified_literals = set([-var if assigned_value == True else var for var, assigned_value in assignments])   # make a set containing the literals that are falsified by the assignments
    for clause in original_formula:
        if set(clause).issubset(falsified_literals):    # True if clauses are a subset of the falsified literals
            return True
    # none of the clauses are a subset of the falsified literals
    return False

def is_empty_formula_mf() -> bool:  # mother fucker
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

    global original_formula, assignments  # using global assignments and formula
    f = copy(original_formula)
    # remove clauses that were made true by the assignment
    for var, assigned_value in assignments:
        removes_clause_from_formula = -1 * var if assigned_value == False else var    # same here
        f = [clause for clause in f if not removes_clause_from_formula in clause]   # that's all the clauses that do not contain the literal that removes them from the formula
    return len(f) == 0

def eliminate_pure_literals_mf(): # mf = memory friendly, obviously
    """Adds the assignments for pure literal elimination to the global list of assignments.
    """

    # get current formula
    global assignments
    # get assignments for elimination
    for literal in get_pure_literals_mf():
        var = abs(literal)
        assigned_value = True if literal > 0 else False
        assignments.append((var, assigned_value))

def get_pure_literals_mf() -> List[int]:    # mf = memory friendly, obviously
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

    global original_formula, assignments
    # first make a list of all the literals
    literals = []

    for clause in original_formula:
        for literal in clause:
            if not literal in literals:
                literals.append(literal)
    
    assigned_vars = [var for var, assigned_value in assignments]
    # now return a list of all the pure literals (a literal is in the list below if it is in the literals list, but it's negated part is not (and it's not already been assigned))
    return [literal for literal in literals if not -literal in literals and not abs(literal) in assigned_vars]

if __name__ == "__main__":
    main()