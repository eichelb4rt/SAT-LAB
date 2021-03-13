#!/bin/python3
# SHEBANG

import os, sys, argparse
from copy import deepcopy, copy
from typing import List, Tuple, Optional

# add the 2-SAT directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
import read_dimacs as dimacs    # no vscode, you're wrong. This is not an unresolved import. fucker.
from data_structures import Clause, Formula, Assignment, Assignments, Trail

# global variables
assignments: Assignments
original_formula: Formula
trail: Trail

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
        lines = f.readlines()
        formula = dimacs.read_cnf(lines)    # reads the formula from the given dimacs encoding
        variables = dimacs.get_variables_in_dimacs(lines)   # gets the number of variables from the given dimacs encoding
    global original_formula, assignments
    original_formula = formula
    assignments = [None for variable in range(variables)]   # prepare assignments
    print(cdcl_solver(), assignments)

def cdcl_solver() -> bool:
    """CDCL with preprocessing.

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """

    # pre-processing
    # UP
    # TODO: UP
    # check for TERMINATION
    if is_empty_formula_mf():
        return True
    if empty_set_contained_mf():
        return False
    # the real thing
    return cdcl_preprocessed()

def cdcl_preprocessed() -> bool:
    """CDCL assuming the formula was preprocessed

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """
    global assignments, original_formula    # we're using these global variables
    decision_level = 0
    while var := get_var_mf():  # while we find new variables
        decision_level -=- 1    # chad += 1
        decide(var) # adds assignment to trail
        while conflict_clause := propagate():  # while we find new conflicts (propagate returns conflict clause or None)
            if decision_level == 0:
                return False    # UNSAT
            learned_clause = analyse_conflict(conflict_clause)  # the clause that is supposed to be learned from the derived conflict
            learn(learned_clause)   # learn the clause
            backtrack(learned_clause)   # start backtracking, depends on learned clause
        apply_restart_policy()  # maybe restart
    return True # SAT



# =======================================================================================
# ================================ UP + watched literals ================================
# =======================================================================================

def propagate() -> Optional[Clause]:    # TODO: fix problem: if a literal is in 2 unit clauses, it is satisfied twice
    """Unit propagation until a conflict is derived.

    Returns
    -------
    Optional[Clause]
        The conflict clause, None if no conflict happened.
    """

    global assignments
    latest_decision = trail[trail.decision_level].decision
    unit_clauses = get_new_unit_clauses(latest_decision)
    # propagate until a conflict is derived or we have no unit clauses left
    while len(unit_clauses) != 0:
        unit_clause = unit_clauses[0]   # take the first unit clause
        # figure out the only unassigned literal in the unit clause
        for literal in unit_clause.watched_literals:
            if assignments.value(literal) is None:
                unit = literal  # unit is the only unassigned literal in the clause
        # !!! the unit clause could have been satisfied because of another unit clause already !!! (rare tho?)
        if not unit:    # if the clause doesn't have an unassigned literal anymore (if it was satisfied, because conflicts are caught earlier on, when the assignment is applied)
            unit_clauses.remove(unit_clause)
            continue
        # figure out the assignment to satisfy the unit
        var = abs(unit)
        value = True if unit > 0 else False
        new_assignment = Assignment(var, value)
        # apply the assignment and add it to the trail - the unit clause is the reason for the assignment.
        assignments.assign(new_assignment)  # apply the assignment
        trail.add_propagation(new_assignment, unit_clause)  # add it to the trail
        # check if a conflict was derived anywhere (a conflict can only be derived in unit clauses)
        for possible_conflict_clause in unit_clauses:
            if is_conflict(possible_conflict_clause):
                return possible_conflict_clause
        # none was found - add the new unit clauses to the list
        for new_unit_clause in get_new_unit_clauses(new_assignment):
            unit_clauses.append(new_unit_clause)
        # remove the satisfied unit clause from the list
        unit_clauses.remove(unit_clause)
        # go again with another unit clause
    # there are no more unit clauses left and no conflict was derived
    return None

def get_new_unit_clauses(assignment: Optional[Assignment]) -> List[Clause]:
    """Changes the 'watched literals' data structure to fit the new assignment and return the clauses that became unit.

    Parameters
    ----------
    assignment : Optional[Assignment]
        The latest applied assignment.

    Returns
    -------
    List[Clause]
        A list of clauses that became unit after the application of the given assignment.
    """

    global original_formula

    # assignment is None for decision level 0
    if assignment is None:  # on decision level 0, return all the clauses that are 1 wide
        return [clause for clause in original_formula if len(clause) == 1]
    # return all the clauses that become unit
    return [clause for clause in original_formula if becomes_unit(clause, assignment)]

def is_conflict(clause: Clause) -> bool:
    """Checks if the given clause is a conflict under the current assignment or not.

    Parameters
    ----------
    clause : Clause
        The given clause.

    Returns
    -------
    bool
        True if the clause is a conflict under the current assignment, False otherwise.
    """

    global assignments
    for literal in clause.watched_literals: # the clause is a conflict if and only if both watched literals are false
        if not assignments.value(literal) is False:
            return False    # one of the watched literals is not False -> no conflict
    return True

def becomes_unit(clause: Clause, assignment: Assignment) -> bool:
    """Checks the invariant and returns if the clause became unit or not. May change the watched literals.

    Parameters
    ----------
    clause: Clause
        The clause that maybe became unit.
    assignment: Assignment
        The latest assignment.

    Returns
    -------
    bool
        True if the clause became unit, false otherwise.
    """

    global assignments  # we need to know about the current assignments
    # check if clause only has 1 literal in the first place
    if len(clause) == 1:
        return False    # TODO: figure out if this is ok
    # check if assignment changes watched literals
    if assignment.var not in [abs(literal) for literal in clause.watched_literals]:
        return False    # assignment variable does not change value of watched literals -> not a new unit clause
    # check if invariant is maintained:
    # check if at least one watched literal is true
    for literal in clause.watched_literals:
        if assignments.value(literal) is True:
            return False    # invariant holds -> clause did not become unit
    # check if both watched literals are unassigned
    both_unassigned = True
    for literal in clause.watched_literals:
        if not assignments.value(literal) is None:
            both_unassigned = False
    if both_unassigned:
        return False    # invariant holds -> clause did not become unit
    # find out which of the 2 watched literals was falsified
    for literal in clause.watched_literals:
        if assignments.value(literal) is False:
            falsified_literal = literal
    watched_literal_index = clause.watched_literals.index(falsified_literal)  # is it the first or the second watched literal?
    # find a new unassigned literal to watch as our currently watched literal is falsified
    # we start looking just after the one that we currently watch and go one full loop around the whole clause
    offset = clause.literals.index(falsified_literal) + 1 # index of the falsified literal in the clause + 1
    for literal in clause.literals_iter(offset):
        if literal not in clause.watched_literals and not assignments.value(literal) is False: # we found an unassigned (or satisfied) literal that is not already being watched
            clause.watched_literals[watched_literal_index] = literal  # so we can watch it
            return False    # that means invariant is maintained and clause not unit
    # if we didn't find an unassigned (or satisfied), unwatched literal, the invariant is broken and the clause became unit
    return True



# ==========================================================================
# ================================ restarts ================================
# ==========================================================================

def apply_restart_policy():
    """Applies the restart policy.
    """

def backtrack(clause: List[int]):
    """Changes trail and decision level for non-chronological backtracking depending on the learned clause.

    Parameters
    ----------
    clause : List[int]
        The learned clause.
    """



# =================================================================================
# ================================ clause learning ================================
# =================================================================================

def learn(clause: List[int]):
    """Learns a given clause.

    Parameters
    ----------
    clause : List[int]
        The clause that is supposed to be learned.
    """

def analyse_conflict(conflict_clause: List[int]) -> List[int]:
    """Analyses the current conflict.

    Parameters
    ----------
    conflict_clause : List[int]
        The conflict that was just found.

    Returns
    -------
    List[int]
        The clause to be learned.
    """


def decide(var: int):
    """Decides the value of a given variable and adds the assignment to the trail.

    Parameters
    ----------
    var : int
        The variable to be decided.
    """

    global assignments # we're using these global variables
    # decide true TODO: real decision
    assignments.append((var, True))



# ====================================================================================
# ================================ mf stuff from DPLL ================================
# ====================================================================================

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