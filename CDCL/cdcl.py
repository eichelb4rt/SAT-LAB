#!/bin/python3
# SHEBANG

import os, sys, argparse
from copy import deepcopy, copy
from typing import List, Tuple, Optional
from collections import deque
import random

# add the 2-SAT directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
import read_dimacs as dimacs    # no vscode, you're wrong. This is not an unresolved import. fucker.
from stats import CDCLStats, StatsAgent
from data_structures import Clause, Formula, Assignment, Assignments, Trail, VSIDS
import config

# global variables
original_formula: Formula
assignments: Assignments
vsids: VSIDS
trail = Trail()
restart_counter = 0
conflict_counter_restarts = 0
# stats
STATS = CDCLStats()

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
            print(f"Assignments:\n{assignments}")
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
        formula = dimacs.read_cnf(lines)    # still in form List[List[int]]
        n = dimacs.get_variables_in_dimacs(lines)   # number of variables
    global original_formula, assignments, vsids, STATS
    # convert to form Formula
    clauses = [Clause(clause) for clause in formula]
    original_formula = Formula(clauses)
    # instantiate assignments and vsids
    assignments = Assignments(n)
    vsids = VSIDS(n)
    # start measuring stuff
    STATS.start()
    # do the thing
    satisfiable = cdcl_solver()
    # stop measuring stats
    STATS.stop()
    return satisfiable

def cdcl_solver() -> bool:
    """CDCL with preprocessing.

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """

    global original_formula
    # pre-processing
    # trivial: empty clause contained?
    for clause in original_formula:
        if len(clause) == 0:
            return False
    # UP
    if conflict := propagate():
        return False
    # did this already satisfy?
    if is_empty_formula():
        return True
    # the real thing
    return cdcl_preprocessed()

def is_empty_formula() -> bool:
    """Determines whether a formula f is empty.

    Returns
    -------
    bool
        True if empty, False if not.
    """

    global original_formula, assignments  # using global assignments and formula
    f = copy(original_formula)
    # remove clauses that were made true by the assignment
    for assignment in assignments.assignment_view:
        removes_clause_from_formula = -1 * assignment.var if assignment.value == False else assignment.var    # == False for readability
        f = [clause for clause in f if not removes_clause_from_formula in clause]   # that's all the clauses that do not contain the literal that removes them from the formula
    return len(f) == 0

def cdcl_preprocessed() -> bool:
    """CDCL assuming the formula was preprocessed

    Returns
    -------
    bool
        True if the global formula is satisfiable, false if not.
    """
    global assignments, original_formula, trail    # we're using these global variables

    while var := select_variable():  # while we find new variables
        decide(var) # decide the variable and do all the dirty work that comes with it
        while conflict_clause := propagate():  # while we find new conflicts (propagate returns conflict clause or None)
            if trail.decision_level == 0:
                return False    # UNSAT
            learned_clause = analyse_conflict(conflict_clause)  # the clause that is supposed to be learned from the derived conflict
            learn(learned_clause)   # learn the clause
            backtrack(learned_clause)   # start backtracking, depends on learned clause
        apply_restart_policy()  # maybe restart
    return True # SAT



# =======================================================================================
# ================================ UP + watched literals ================================
# =======================================================================================

def propagate() -> Optional[Clause]:
    """Unit propagation until a conflict is derived.

    Returns
    -------
    Optional[Clause]
        The conflict clause, None if no conflict happened.
    """

    # only use this method if watched literals are turned on
    if not config.WATCHED_LITERALS:
        return basic_propagate()
    # here the actual method
    
    global assignments, trail, STATS
    highest_decision_level = trail.decision_level
    latest_assignment = (trail[highest_decision_level]).get_latest_assignment()
    unit_clauses = deque(get_new_unit_clauses(latest_assignment))
    # propagate until a conflict is derived or we have no unit clauses left
    while unit_clauses:
        unit_clause = unit_clauses.popleft()
        # figure out the only unassigned literal in the unit clause
        unit = None
        for literal in unit_clause.watched_literals:
            if assignments.value(literal) is None:
                unit = literal  # unit is the only unassigned literal in the clause
        # !!! the unit clause could have been satisfied because of another unit clause already !!! (rare tho?)
        if not unit:    # if the clause doesn't have an unassigned literal anymore (if it was satisfied, because conflicts are caught earlier on, when the assignment is applied)
            continue    # unit clause was already removed by popleft()
        # figure out the assignment to satisfy the unit
        var = abs(unit)
        value = True if unit > 0 else False
        new_assignment = Assignment((var, value), trail.decision_level)
        # apply the assignment and add it to the trail - the unit clause is the reason for the assignment.
        assignments.assign(new_assignment, unit_clause)  # apply the assignment
        trail.add_propagation(new_assignment, unit_clause)  # add it to the trail
        STATS.propagate()   # gotta count the UP
        # check if a conflict was derived anywhere (a conflict can only be derived in unit clauses)
        for possible_conflict_clause in unit_clauses:
            if is_conflict(possible_conflict_clause):
                STATS.conflict()    # gotta count these conflicts
                return possible_conflict_clause
        # none was found - add the new unit clauses to the list
        unit_clauses.extend(get_new_unit_clauses(new_assignment))
        # go again with another unit clause
    # there are no more unit clauses left and no conflict was derived
    return None

def get_new_unit_clauses(assignment: Optional[Assignment]) -> List[Clause]: # TODO: we might be able to make this more efficient with 'watched clauses'
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

    global STATS, conflict_counter_restarts, restart_counter, assignments, trail, vsids
    # restart if the number of conflicts since the last restart has reached the limit
    # the limit is the luby sequence with index = number of restarts + 1 (so that the first restart has index 1) scaled
    if conflict_counter_restarts >= luby_sequence(restart_counter + 1) * config.SCALE_LUBY:
        # count the restart
        restart_counter -=- 1   # chad += 1
        STATS.restart()
        # wipe assignments, trail, vsids counters (basically everything but the learned clauses)
        n = len(assignments)    # number of variables
        assignments = Assignments(n)
        vsids = VSIDS(n)
        trail = Trail()

def luby_sequence(i: int) -> int:
    """The luby sequence at a given index i. Simple and recursive.
    Note: starts at 1.

    Parameters
    ----------
    i : int
        The given index.

    Returns
    -------
    int
        The element of the luby sequence at index i.
    """

    # find out if there is a k so that i = 2**k - 1
    k = 0
    while 2**k - 1 < i:
        k -=- 1 # chad +=
    # we found out and know k
    if i == 2**k - 1:
        return 2**(k - 1)
    else: # i < 2**k - 1
        return luby_sequence(i - 2**(k-1) + 1)



# ==============================================================================
# ================================ backtracking ================================
# ==============================================================================

def backtrack(clause: List[int]):
    """Changes trail and decision level for non-chronological backtracking depending on the learned clause.

    Parameters
    ----------
    clause : List[int]
        The learned clause.
    """

    # only use this method if UIP learning is turned on
    if not config.LEARN_UIP:
        return basic_backtrack(clause)
    # here the actual method

    global assignments, trail, STATS
    # find out the asserting level: the max decision level that includes learned literals. The highest decision level is excluded!
    asserting_level = 0
    for literal in clause:
        level = assignments.decision_level(abs(literal))
        if level > asserting_level and level != trail.decision_level:
            asserting_level = level
    backtrack_to(asserting_level)
    # since we learned the 1UIP and we jumped to the asserting level, we can safely satisfy the learned clause with unit propagation
    # first of all find out which one of the variables is now going to be propagated
    unit = 0
    for literal in clause:
        if assignments[abs(literal)] is None:
            unit = literal
    # satisfy the unit clause
    # figure out the assignment to satisfy the unit
    var = abs(unit)
    value = True if unit > 0 else False
    # assign the literal on the asserting decision level
    new_assignment = Assignment((var, value), asserting_level)
    assignments.assign(new_assignment, clause)  # apply the assignment
    trail.add_propagation(new_assignment, clause)  # add it to the trail
    STATS.propagate()
        

def backtrack_to(level: int):
    """Changes trail and decision level for backtracking to the given level.

    Parameters
    ----------
    level : int
        The given level.
    """

    global assignments, trail

    # unassign variables
    for decision_level in trail[level + 1:]:    # includes level + 1 , ... , highest decision level
        for assignment in decision_level.assignments: # the assignments on the decision level
            del assignments[assignment.var] # unassign the variable
    # reset trail
    trail.backtrack(level)



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

    global original_formula
    original_formula.learn(clause)
    STATS.learn()   # gotta count those learned clauses

def analyse_conflict(conflict_clause: Clause) -> Clause:
    """Analyses the current conflict.

    Parameters
    ----------
    conflict_clause : Clause
        The conflict that was just found.

    Returns
    -------
    Clause
        The clause to be learned.
    """

    # only use this method if UIP learning is turned on
    if not config.LEARN_UIP:
        return basic_analyse_conflict(conflict_clause)
    # here the actual method

    global trail
    assignments_on_decision_level = trail[trail.decision_level].assignments
    #variables_on_decision_level = [assignment.var for assignment in assignments_on_decision_level]
    cut = conflict_clause   # initiate the cut with the conflict clause
    conflict_zone = []  # the variables in the conflict zone of the cut
    imp_graph = implication_graph_on_decision_level()   # the implication graph only on the highest decision level
    dec_vars = deque(variables_on_decision_level(cut, trail.decision_level))   # dec_vars is now the list of variables on the last decision level (in the cut)
    while len(dec_vars) > 1:    # while there is more than 1 literal on the highest decision level in the current clause, keep going
        pivot = dec_vars.popleft()  # the first variable in the list will be our pivot
        # now check if the pivot can reach any other variables in the cut
        # we do this with DF search:
        others_reachable = False
        open_list = deque([pivot]) # initiate the open list (nodes to be expanded)
        while open_list:    # while there are nodes in the open list
            node = open_list.popleft() # node to be expanded - the first node in the list (we append new nodes at the end)
            if node in conflict_zone:
                pass    # node stays removed
                # we don't need to look past the cut
            elif not node is pivot and node in dec_vars:    # if a node is in the cut and is not the pivot itself (not node is pivot is actually not needed here, because popleft() removes it from the list, but this makes a bit clearer that this might be needed if we change the implementation)
                others_reachable = True # then another variable in the cut is reachable
                break
            else:   # node is not in cut and not in conflict zone -> expand it
                # node is already removed from the start
                open_list.extend(imp_graph[node])   # append it's direct successors
        # we found out if other variables in the cut are reachable from the pivot
        if others_reachable:
            # go to the end of the queue!
            dec_vars.append(pivot)
            continue    # and look at the next variable - continue is actually not needed here, just for readability
        else:   # we can't reach any variables outside the cut if we add this to the cut, so let's just do that shall
            reason = assignments.reason(pivot)  # reason clause for assignment of pivot
            cut = resolve(cut, reason, pivot)    # resolve the reason with the cut
            new_decision_variables = variables_on_decision_level(reason, trail.decision_level)  # the new variables that are now in the cut on the highest decision level
            new_decision_variables = [variable for variable in new_decision_variables if variable not in dec_vars and not variable is pivot]    # only add actually new variables. we do not want duplicates.
            dec_vars.extendleft(new_decision_variables)  # add the new decision variables on the left (the ones on the right could reach other variables in our cut before and probably still can)
            conflict_zone.append(pivot) # the pivot is now in the conflict zone
    # we resolved until there was only 1 literal on the highest decision level left. This is the 1UP. This is the way.
    return cut

def resolve(a: Clause, b: Clause, pivot: int) -> Clause:
    """Resolution of clauses a and b with a given pivot.

    Parameters
    ----------
    a : Clause
        The given clause a.
    b : Clause
        The given clause b.
    pivot : int
        The pivot for the resolution.

    Returns
    -------
    Clause
        Resolution boiiiis. Can't repeat it enough.
    """

    # every literal from a and b is in there except for the pivoted variable
    literals = [literal for literal in a.literals + b.literals if abs(literal) != pivot]
    return Clause(literals)

def implication_graph_on_decision_level() -> dict:
    """Returns the implication graph on the highest decision level (only the highest decision level!).

    Returns
    -------
    dict
        Adjancency list of the implication graph (a: [b,c]) if a's direct successors are b and c.
    """

    global trail
    adjacency_list = {}
    assignments_on_level = trail[trail.decision_level].assignments  # the variables that were assigned on the latest decision level
    # initialise the list for every variable
    for assignment in assignments_on_level:
        adjacency_list[assignment.var] = []
    # draw the lines
    propagations = trail[trail.decision_level].propagations # only propagations have predecessors
    for propagation in propagations:
        # the direct predecessor of a variable is every variable that's in the reason clause except for the assignment var itself
        predecessors = variables_on_decision_level(propagation.reason, trail.decision_level) # we only care for variables on the highest decision level
        predecessors.remove(propagation.assignment.var) # except for the assignment var itself
        # append assignment var to the lists of the predecessor
        for predecessor in predecessors:
            adjacency_list[predecessor].append(propagation.assignment.var)
    return adjacency_list

def variables_on_decision_level(clause: Clause, level: int) -> List[int]:
    """Returns the list of variables in given clause that are on the given decision level.

    Parameters
    ----------
    clause : Clause
        The given clause.
    
    level : int
        The given decision level.

    Returns
    -------
    List[int]
        The list of variables in the clause that were assigned on the given decision level.
    """

    global trail
    variables_on_level = [assignment.var for assignment in trail[level].assignments] # the variables that were assigned on the given decision level
    return [abs(literal) for literal in clause if abs(literal) in variables_on_level]



# ===========================================================================
# ================================ decisions ================================
# ===========================================================================

def select_variable() -> Optional[int]:
    """Decides which variable to select for a decision.

    Returns
    -------
    Optional[int]
        The selected variable. None if every variable is assigned.
    """

    # only use this method if watched literals are turned on
    if not config.VSIDS:
        return basic_selection()
    # here the actual method
    
    global vsids, assignments
    max_index = None   # index of the variable with the max counter
    max_counter = -1 # max counter
    for index, counter in enumerate(vsids.counters):
        # if there's a higher scoring variable that is not assigned yet, we prefer it
        if counter > max_counter and assignments[index + 1] is None:    # index (x) -> variable (x + 1)
            max_index = index
            max_counter = counter
    if not max_index is None:
        return max_index + 1   # index (x) -> variable (x + 1)
    return None

def decide(var: int):
    """Decides the value of a given variable and adds the assignment to the trail.

    Parameters
    ----------
    var : int
        The variable to be decided.
    """

    global assignments, trail # we're using these global variables
    value = variable_decision_heuristic(var)    # what value should be assigned to the variable
    assignment = Assignment((var, value), trail.decision_level + 1)   # assignment as the type Assignment - will be on a new decision level!
    assignments.assign(assignment)  # add the assignment to the list of assignments
    trail.decide(assignment)    # add it to the trail
    STATS.decide()  # gotta count those decisions

def variable_decision_heuristic(var: int) -> bool:
    """The suggested value for a given variable.

    Parameters
    ----------
    var : int
        The given variable.

    Returns
    -------
    bool
        The suggested value for the variable assignment.
    """

    # only use this method if the variable decision heuristic is turned on
    if not config.DECISION_HEURISTIC:
        return basic_decision(var)
    # here the actual method
    
    global assignments
    # we want to maintain the last assignment
    if assignments.last_assignment(var) is None:
        return True
    else:
        return assignments.last_assignment(var)



# =======================================================================================
# ================================ basic implementations ================================
# =======================================================================================

def basic_decision(var: int) -> bool:
    """The suggested value for a given variable. Picks randomly.

    Parameters
    ----------
    var : int
        The given variable.

    Returns
    -------
    bool
        The suggested decision.
    """

    return random.choice([True, False])

def basic_selection() -> Optional[int]:
    """Decides which variable to select for a decision. Very basic.

    Returns
    -------
    Optional[int]
        The selected variable. None if every variable is assigned.
    """

    global assignments
    for assignment in assignments.assignment_view:
        if assignment.value is None:
            return assignment.var
    return None

def basic_propagate() -> Optional[Clause]:
    """Basic unit propagation until a conflict is derived.

    Returns
    -------
    Optional[Clause]
        The conflict clause, None if no conflict happened.
    """

    global assignments, trail, STATS
    # propagate until a conflict is derived or we have no unit clauses left
    while unit_clauses := basic_get_unit_clauses():
        unit_clause = unit_clauses[0]
        # figure out the only unassigned literal in the unit clause
        unit = None
        for literal in unit_clause:
            if assignments.value(literal) is None:
                unit = literal  # unit is the only unassigned literal in the clause
        # figure out the assignment to satisfy the unit
        var = abs(unit)
        value = True if unit > 0 else False
        new_assignment = Assignment((var, value), trail.decision_level)
        # apply the assignment and add it to the trail - the unit clause is the reason for the assignment.
        assignments.assign(new_assignment, unit_clause)  # apply the assignment
        trail.add_propagation(new_assignment, unit_clause)  # add it to the trail
        STATS.propagate()   # gotta count the UP
        # check if a conflict was derived anywhere (a conflict can only be derived in unit clauses)
        for possible_conflict_clause in unit_clauses:
            if basic_is_conflict(possible_conflict_clause):
                STATS.conflict()    # gotta count these conflicts
                return possible_conflict_clause
        # go again with another unit clause
    # there are no more unit clauses left and no conflict was derived
    return None

def basic_get_unit_clauses() -> List[Clause]:
    """Gets unit clauses in a very basic way without watched literals.

    Returns
    -------
    List[Clause]
        The clauses that are unit under the current assignment.
    """

    global original_formula
    return [clause for clause in original_formula if basic_is_unit(clause)]

def basic_is_unit(clause: Clause) -> bool:
    """Basic check if the clause is unit under the current assignment.

    Parameters
    ----------
    clause : Clause
        The given clause.

    Returns
    -------
    bool
        True if the clause is unit, False otherwise.
    """

    global assignments
    unassigned_literals = [literal for literal in clause if assignments.value(literal) is None]
    has_satisfied_literal = False
    for literal in clause:
        if assignments.value(literal) is True:
            has_satisfied_literal = True
            break
    return not has_satisfied_literal and len(unassigned_literals) == 1  # if we only have 1 unassigned literal and no satisfied literals, it's unit

def basic_is_conflict(clause: Clause) -> bool:
    """Checks if the given clause is a conflict under the current assignment or not (without watched literals).

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
    for literal in clause: # the clause is a conflict if and only if both watched literals are false
        if not assignments.value(literal) is False:
            return False    # one of the watched literals is not False -> no conflict
    return True

def basic_backtrack(clause: List[int]):
    """Changes trail and decision level for non-chronological backtracking depending on the learned clause.

    Parameters
    ----------
    clause : List[int]
        The learned clause.
    """

    global trail
    basic_backtrack_to(trail.decision_level - 1)    # yeah we don't even care about the clause. We're wandering through our lives without care!

def basic_backtrack_to(level: int):
    """Changes trail and decision level for backtracking to the given level.

    Parameters
    ----------
    level : int
        The given level.
    """

    global assignments, trail

    # unassign variables in higher levels
    for decision_level in trail[level + 1:]:    # includes level + 1 , ... , highest decision level
        for assignment in decision_level.assignments: # the assignments on the decision level
            del assignments[assignment.var] # unassign the variable
    # unassign all the propagated variables
    for propagation in trail[level].propagations:
        del assignments[propagation.assignment.var]
    # reset trail
    trail.trail = trail.trail[:level + 1]   # erase higher levels
    trail[level].propagations = []  # erase all propagated variables

def basic_analyse_conflict(conflict_clause: Clause) -> Clause:
    """Analyses the current conflict. Very basic.

    Parameters
    ----------
    conflict_clause : Clause
        The conflict that was just found.

    Returns
    -------
    Clause
        The clause to be learned.
    """

    global trail
    learned_literals = []
    for level in trail:
        if level.decision:  # not 0th decision level
            literal_learned = -level.decision.var if level.decision.value else level.decision.var
            learned_literals.append(literal_learned)
    return Clause(learned_literals)

if __name__ == "__main__":
    main()