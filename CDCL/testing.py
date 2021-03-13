from typing import List, Tuple, Optional
from copy import deepcopy, copy
from collections.abc import Sequence, Collection, MutableSequence
from data_structures import Formula, Clause, Assignments, Assignment, Trail
import cdcl

# global variables
clauses_array_form = [[-1, 2], [-1, -2]]
assignments = Assignments(3)
original_formula: Formula = [Clause(literals) for literals in clauses_array_form]
trail = Trail()

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
        new_assignment = Assignment((var, value))
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

print(propagate())
assignments.assign(Assignment((1, True)))
trail.decide(Assignment((1, True)))
print(propagate())