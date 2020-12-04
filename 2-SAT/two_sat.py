#!/bin/python3
# SHEBANG

import os
import sys
import time
import random
import argparse
import tracemalloc
import numpy as np
from copy import deepcopy
import read_dimacs as dimacs
from tabulate import tabulate
from typing import List, Tuple

# decided to go with global variables because returning these sums through the whole structure 
# of functions would lead to unnecessarily complicated return types and function calls
number_of_decisions = 0
number_of_propagations = 0

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
    for clause in formula:
        # check if it follows the rules like a good boi
        if len(clause) > 2:
            sys.stderr.write("This formula does not follow the rules of 2-SAT.")
            sys.exit(1)
    
    # prepare measuring of stats
    if args.show_stats:
        start_time = time.process_time()
        tracemalloc.start()
    # now finally do the thing
    satisfiable, assignments = two_sat(formula)
    # stop measuring of stats
    if args.show_stats:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        time_elapsed = time.process_time() - start_time

    # print results
    if satisfiable:
        print("Satisfiable")
        if args.show_assignments:
            print(f"Assignments:\n{assignments}")
    else:
        print("Unsatisfiable")
    
    # print stats
    if args.show_stats:
        stats = [
            ["Peak Memory Usage",   f"{round(peak / 10**6, 2)} MB"],
            ["Process time",        f"{round(time_elapsed, 2)} s"],
            ["Number of decisions",     number_of_decisions],
            ["Number of propagations",  number_of_propagations]
        ]
        print(tabulate(stats))

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

    # preprocessing
    # find a unit clause
    if literal := find_unit_clause(f):
        var = abs(literal)
        assigned_value = True if literal > 0 else False # figure out what value it should be assigned to make it true
        f = unit_propagation(f, (var, assigned_value))  # unit propagation

    if empty_set_contained(f):
        return False, None

    # loop
    assignments = []
    global number_of_decisions
    while var := get_var(f):  # while vars(f) != empty set
        # decision time - gotta count it
        number_of_decisions -=- 1 # cooler than +=
        # assign 0 to the var and propagate
        new_f, new_assignments = unit_propagation(apply_assignment(f, (var, False)))
        if empty_set_contained(new_f):  # empty set is contained
            # assign 1 to the var
            new_f, new_assignments = unit_propagation(apply_assignment(f, (var, True)))
            if empty_set_contained(new_f):
                return False, None
        f = new_f
        for assignment in new_assignments:
            assignments.append(assignment)
    # vars(f) == empty set
    return True, assignments

def get_var(f: List[List[int]]) -> int:
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

def unit_propagation(f) -> (List[List[int]], List[Tuple[int, bool]]):
    """Applies unit propagation to the given formula.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.

    Returns
    -------
    (List[List[int]], List[Tuple[int, bool])
        The given formula with unit propagation applied and the assignments that were propagated.
    """

    # deep copy as we don't want to change f or the clauses in f
    f = deepcopy(f)
    # apply the given assignment
    assignments = []  # add it to the list of assignments

    # propagate
    global number_of_propagations
    while literal := find_unit_clause(f): # while unit clauses are found
        # propagation time - gotta count it
        number_of_propagations -=- 1  # chad version of += 1
        # assign value so that it makes the literal in the unit clause true
        assigned_value = True if literal > 0 else False
        # apply the propagated assignment
        assignment = (abs(literal), assigned_value)
        assignments.append(assignment)
        f = apply_assignment(f, assignment)
    return f, assignments

def find_unit_clause(f: List[List[int]]) -> int:
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