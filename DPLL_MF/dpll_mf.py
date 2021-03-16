#!/bin/python3
# SHEBANG

import os, sys, time, argparse, tracemalloc
from copy import deepcopy, copy
from typing import List, Tuple, Optional
from tabulate import tabulate

# add the global_libs directory for general functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
import read_dimacs as dimacs
from stats import DPLLStats, StatsAgent
# add 2-SAT directory for unit propagation and application of assignments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}2-SAT")
from two_sat import unit_propagation, apply_assignment

# global variables the algorithm uses
assignments_view = []   # [(var, bool)] - order of assignment
assignments = []    # fast access variable assignment - variable (x) stored at index (x-1)
original_formula = []
# global variables for stats
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

    global STATS
    # solve the thing
    satisfiable = solve_input(args.input)
    # print results
    if satisfiable:
        print("Satisfiable")
        if args.show_assignments:
            print(f"Assignments:\n{assignments_view}")
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
    
    with open(input, "r") as f:
        lines = f.readlines()
        formula = dimacs.read_cnf(lines)
        n = dimacs.get_variables_in_dimacs(lines)   # number of variables
    global original_formula, assignments_view, assignments, STATS
    original_formula = formula
    assignments = [None] * n
    assignments_view = []
    # solve and measure stuff
    STATS.start()
    # now finally do the thing
    satisfiable = dpll_solver()
    # stop measuring of stats
    STATS.stop()
    return satisfiable

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
    global assignments, assignments_view, original_formula, STATS   # we're using these global variables
    unit_propagation_mf()   # unit propagation
    eliminate_pure_literals_mf()    # eliminate pure literals
    # check for TERMINATION by Arnold Schwarzenegger
    if is_empty_formula_mf():
        return True
    if empty_set_contained_mf():
        return False
    
    var = get_var_mf()  # Oh i'd like some sweet variables now. Wanna go get some?
    # recursion go brr
    entry_point = len(assignments_view)  # entry point is the index of the next variable to be assigned
    assignments_view.append((var, False))    # assign(var, 0)
    assignments[var - 1] = False
    STATS.decide()  # we decided something and we're gonna stick with it!
    if dpll_mf():
        return True
    backtrack(entry_point)
    # ite, let's just try it again, shall we?
    assignments_view.append((var, True))    # assign(var, 1)
    assignments[var - 1] = True
    STATS.decide()  # ok maybe we won't stick with all of our decisions
    if dpll_mf():
        return True
    backtrack(entry_point)
    return False

def backtrack(entry_point: int):
    """Backtracks to the entry point. Unassigns every variable after (included) the entry point.
    """

    global assignments, assignments_view
    for assignment in assignments_view[entry_point:]:
        assignments[assignment[0] - 1] = None
    assignments_view = assignments_view[:entry_point] # unassign(x)

def get_var_mf() -> Optional[int]: # mf = memory friendly, obviously
    """Gets a variable from the formula.

    Returns
    -------
    Optional[int]
        Returns an unassigned variable from the formula, None if none was found.
    """

    global original_formula, assignments_view
    for index, value in enumerate(assignments):
        if value is None:
            return index + 1
    return None

def unit_propagation_mf():  # mf = memory friendly, obviously
    """Applies unit propagation and adds the assigned assignments to the global list of assignments.
    """

    global original_formula, assignments_view, assignments, STATS # gonna use em both like every time
    while unit_clause := get_unit_clause():
        # get the unit
        unit = None
        for literal in unit_clause:
            var = abs(literal)
            index = var - 1
            if assignments[index] is None:
                unit = literal
                break
        # assignment that satisfied unit literal
        value = True if literal > 0 else False
        var = abs(literal)
        index = var - 1
        new_assignment = (var, value)
        # apply the assignment
        assignments_view.append(new_assignment)
        assignments[index] = value
        STATS.propagate()

def get_unit_clause() -> Optional[List[int]]:
    """Gets a unit clause.

    Returns
    -------
    Optional[List[int]]
        A unit clause, None if none was found.
    """

    global original_formula
    for clause in original_formula:
        if is_unit_clause(clause):
            return clause
    return None

def is_unit_clause(clause: List[int]) -> bool:
    """Returns if a clause is unit or not.

    Parameters
    ----------
    clause : List[int]
        The given clause.

    Returns
    -------
    bool
        True if it is unit, False otherwise.
    """

    global assignments
    unassigned_literals = [literal for literal in clause if assignments[abs(literal)-1] is None]
    return not clause_satisfied_mf(clause) and len(unassigned_literals) == 1

def empty_set_contained_mf() -> bool:   # mf = memory friendly, obviously
    """Determines whether the formula with the applied assignment contains an empty clause.

    Returns
    -------
    bool
        True if empty set is found.
    """

    global original_formula
    for clause in original_formula:
        if clause_empty_set(clause):
            return True
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

    global original_formula
    for clause in original_formula:
        if not clause_satisfied_mf(clause):
            return False
    return True

def clause_empty_set(clause: List[int]) -> bool:
    """Returns if the clause is the empty set under the global assignment.

    Parameters
    ----------
    clause : List[int]
        The given clause.

    Returns
    -------
    bool
        True if the clause is an empty set under the global assignment, False otherwise.
    """

    global assignments
    for literal in clause:
        var = abs(literal)
        value_to_be_falsified = False if literal > 0 else True
        index = var - 1
        if assignments[index] != value_to_be_falsified:
            return False
    return True

def clause_satisfied_mf(clause: List[int]) -> bool:
    """Returns if the clause is already satisfied by the global assignment.

    Parameters
    ----------
    clause : List[int]
        The given clause.

    Returns
    -------
    bool
        True if it is satisfied by the given assigment, False otherwise.
    """

    global assignments
    for literal in clause:
        var = abs(literal)
        value_to_be_satisfied = False if literal < 0 else True
        index = var - 1
        if assignments[index] == value_to_be_satisfied:
            return True
    return False

def eliminate_pure_literals_mf(): # mf = memory friendly, obviously
    """Adds the assignments for pure literal elimination to the global list of assignments.
    """

    # get current formula
    global assignments_view, assignments, STATS
    # get assignments for elimination
    while literal := get_pure_literal_mf():
        var = abs(literal)
        assigned_value = True if literal > 0 else False
        assignments_view.append((var, assigned_value))
        index = var - 1
        assignments[index] = assigned_value
        STATS.count_pure_literal()

def get_pure_literal_mf() -> List[int]:    # mf = memory friendly, obviously
    """Gets a pure literal in a given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula f.

    Returns
    -------
    int
        All the pure literals. Empty list if none were found.
    """

    global original_formula, assignments_view, assignments

    for index, value in enumerate(assignments):
        var = index + 1
        if value is None:
            # positive and negative occurences of the variables
            occurences = []
            for clause in original_formula:
                if not clause_satisfied_mf(clause): # if the literal can actually be seen
                    literal = None
                    if var in clause:
                        literal = var
                    if -var in clause:
                        literal = -var
                    # if var is in clause
                    if literal:
                        occurences.append(literal)
            # now we look if there is only 1 type of occurence
            for literal in [var, -var]:
                if literal in occurences and not -literal in occurences:    # if it only occurs in 1 form (pos or neg)
                    return literal
    return None

if __name__ == "__main__":
    main()