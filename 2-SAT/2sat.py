#!/bin/python3
# SHEBANG

import os
import sys
import random
import argparse
import numpy as np
import read_dimacs as dimacs
from typing import List, Tuple

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
        formula = dimacs.read_cnf(f.readlines())
        print(two_sat(formula))

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
    if empty_set_contained(f):
        return False
    # loop
    assignments = []
    while var := get_var(f):  # while vars(f) != empty set
        # assign 0 to the var
        new_f, new_assignments = unit_propagation(f, (var, False))
        if empty_set_contained(new_f):  # empty set is contained
            # assign 1 to the var
            new_f, new_assignments = unit_propagation(f, (var, False))
            if empty_set_contained(new_f):
                return False, None
        f = new_f
        for assignment in new_assignments:
            assignments.append(assignment)
    # vars(f) == empty set
    return True, assignments

def get_var(f: List[List[int]]) -> int:
    """Gets a variable in the formula f, preferably a variable in a unit clause.

    Parameters
    ----------
    f : List[List[int]]
        The given forumula.

    Returns
    -------
    int
        Variable in formula, preferably a variable in a unit clause, None if there is no variable left
    """

    if literal := find_unit_clause(f):
        return abs(literal)
    
    # return first variable
    if len(f) != 0:
        if len(f[0]) != 0:
            return f[0][0]
    
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

def unit_propagation(f: List[List[int]], assignment: Tuple[int, bool]) -> (List[List[int]], List[Tuple[int, bool]]):
    """Applies the assignment plus unit propagation to the given formula.

    Parameters
    ----------
    f : List[List[int]]
        The given formula.
    assignment : Tuple[int, bool]
        A variable and the assigned boolean.

    Returns
    -------
    (List[List[int]], List[Tuple[int, bool])
        The given formula with the assignment assigned plus unit propagation and the assignment itself.
    """

    # apply the given assignment
    assignments = [assignment]
    f = apply_assignment(f, assignment)

    # propagate
    while literal := find_unit_clause(f): # while unit clauses are found
        if literal > 0:
            assigned_value = True
        else:
            assigned_value = False
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
        Literal if found in unit clause. 0 if no unit clause was found.
    """

    for clause in f:
        if len(clause) == 1:
            return clause[0]
    return None

def apply_assignment(f: List[List[int]], assignment: Tuple[int, bool]) -> List[List[int]]:
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

    # now to define what literals remove a clause from the formula or the literal from the clause if contained
    var = assignment[0]
    assigned_value = assignment[1]
    removes_literal_from_clause = -1 * var if assigned_value == True else var   # == True just for readability, ik i don't need it
    removes_clause_from_formula = -1 * var if assigned_value == False else var    # same here

    # now remove the things
    edited_formula = True   # to start the loop
    # we're done if we haven't edited any clauses or removed any from the formula
    while edited_formula:
        edited_formula = False  # never set to True if nothing is edited
        for i, clause in enumerate(f):
            if removes_literal_from_clause in clause:
                # remove the literal
                f[i].remove(removes_literal_from_clause)
                edited_formula = True
                break
            elif removes_clause_from_formula in clause: # elif because the cases are mutually exclusive
                # remove the clause
                f.remove(clause)
                edited_formula = True
                break
    return f

if __name__ == "__main__":
    main()