#!/bin/python3
# SHEBANG

import os
import sys
import time
import random
import argparse
import tracemalloc
from copy import deepcopy
from tabulate import tabulate
from typing import List, Tuple, Optional
# add the global_libs directory for general functionality
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
import read_dimacs as dimacs
from stats import TwoSatStats, StatsAgent

# global instance of the stats agent (const)
STATS = TwoSatStats()
# global instance of assignments since solve_input should only return satisfiablity and we somehow need the assignments anyway
global_assignments = []

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
    global STATS, global_assignments

    satisfiable = solve_input(args.input)
    # print results
    if satisfiable:
        print("Satisfiable")
        if args.show_assignments:
            print(f"Assignments:\n{global_assignments}")
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

    with open(input, "r") as new_f:
        formula = dimacs.read_cnf(new_f.readlines())
    for clause in formula:
        # check if it follows the rules like a good boi
        if len(clause) > 2:
            sys.stderr.write("This formula does not follow the rules of 2-SAT.")
            sys.exit(1)
    
    # prepare measuring of stats
    global STATS, global_assignments
    STATS.start()
    # now finally do the thing
    satisfiable, assignments = two_sat(formula)
    # stop measuring of stats
    STATS.stop()
    global_assignments = assignments
    return satisfiable

def two_sat(f: List[List[int]]) -> (bool, List[Tuple[int, bool]]):
    """Applies the 2-SAT algorithm to the given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.

    Returns
    -------
    bool, List[Tuple[int, bool]]
        True plus fulfilling assignment if f is satisfiable, False and None if not.
    """

    # preprocessing, initates assignments
    f, assignments = unit_propagation(f)  # unit propagation
    if empty_set_contained(f):
        return False, None

    # loop
    global STATS
    while var := get_var(f):  # while vars(f) != empty set
        # decision time - gotta count it
        STATS.decide()
        # assign 0 to the var and propagate
        new_f, new_assignments = unit_propagation(apply_assignment(f, (var, False)))
        if empty_set_contained(new_f):  # empty set is contained
            # decision time - gotta count it
            STATS.decide()
            # assign 1 to the var
            new_f, new_assignments = unit_propagation(apply_assignment(f, (var, True)))
            if empty_set_contained(new_f):
                return False, None
        f = new_f
        for assignment in new_assignments:
            assignments.append(assignment)
    # vars(f) == empty set
    return True, assignments

def get_var(f: List[List[int]]) -> Optional[int]:
    """Gets a variable in the formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given forumula.

    Returns
    -------
    int
        Variable in formula, None if there is no variable left.
    """
    
    # return first variable
    for clause in f:
        if len(clause) != 0:  # Actually not needed for 2-SAT, because an empty clause would have been found earlier. Still nice as reusable code tho.
            return abs(clause[0])
    
    return None

def empty_set_contained(f: List[List[int]]) -> bool:
    """Checks if empty set is contained in a given formula.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.

    Returns
    -------
    bool
        True if empty set is contained, False if not.
    """

    for clause in f:
        if len(clause) == 0:
            return True
    return False

def unit_propagation(f: List[List[int]], stats_agent: StatsAgent = globals()["STATS"]) -> (List[List[int]], List[Tuple[int, bool]]):
    """Applies unit propagation to the given formula.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.
    stats_agent: StatsAgent
        The stats agent is also passed as an argument so we can use the method in different modules.
        Default: the global stats_agent

    Returns
    -------
    (List[List[int]], List[Tuple[int, bool])
        The given formula with unit propagation applied and the assignments that were propagated.
    """

    # deep copy as we don't want to change f or the clauses in f
    f = deepcopy(f)
    # init local list of assignments
    assignments = []

    # propagate
    while literal := find_unit_clause(f): # while unit clauses are found
        # propagation time - gotta count it
        stats_agent.propagate() # ! does not use the global one
        # assign value so that it makes the literal in the unit clause true
        assigned_value = True if literal > 0 else False
        # apply the propagated assignment
        assignment = (abs(literal), assigned_value)
        assignments.append(assignment)
        f = apply_assignment(f, assignment)
    return f, assignments

def find_unit_clause(f: List[List[int]]) -> Optional[int]:
    """Finds a unit clause in the given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.

    Returns
    -------
    int
        Literal if found in unit clause. None if no unit clause was found.
    """

    for clause in f:
        if len(clause) == 1:
            return clause[0]
    return None

def apply_assignment(f, assignment: Tuple[int, bool]) -> List[List[int]]:
    """Applies the given assignment to the given formula f.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.
    assignment : Tuple[int, bool]
        A variable and the assigned boolean.

    Returns
    -------
    List[List[int]]
        The given formula where the assignment is applied.
    """

    # deep copy as we don't want to change f or the clauses in f
    f = deepcopy(f)
    # now to define what literals remove a clause from the formula or the literal from the clause if contained
    var = assignment[0]
    assigned_value = assignment[1]
    removes_literal_from_clause = -1 * var if assigned_value == True else var   # == True just for readability, ik i don't need it
    removes_clause_from_formula = -1 * var if assigned_value == False else var    # same here

    # first remove clauses
    f = [clause for clause in f if not removes_clause_from_formula in clause]   # that's all the clauses that do not contain the literal that removes them from the formula
    # then remove literals from clauses
    for i, clause in enumerate(f):
        if removes_literal_from_clause in clause:
                f[i].remove(removes_literal_from_clause)
    # we're done
    return f

if __name__ == "__main__":
    main()