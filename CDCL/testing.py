from typing import List, Tuple, Optional
from copy import deepcopy, copy
from collections.abc import Sequence, Collection, MutableSequence
from data_structures import Formula, Clause, Assignments, Assignment, Trail, WatchedClauses
import cdcl

def get_new_unit_clauses(assignment: Assignment) -> List[Clause]:
        """Changes the 'watched literals' data structure to fit the new assignment and return the clauses that became unit.

        Parameters
        ----------
        assignment : Assignment
            The applied assignment.

        Returns
        -------
        List[Clause]
            A list of clauses that became unit after the application of the given assignment.
        """

        global watched_clauses  # we are using the watched clauses data structure to figure out which clauses become unit
        # the literal being falsified by the given assignment:
        literal_falsified = -assignment.var if assignment.value == True else assignment.var    # == True for readability
        possible_clauses = watched_clauses[literal_falsified]   # clauses where the falsified literal is being watched in
        new_unit_clauses = []   # initiate list of new unit clauses
        for clause in possible_clauses:
            # becomes_unit changes the watched literals and determines if the clause becomes true after the falsification of the literal
            if becomes_unit(clause):
                new_unit_clauses.append(clause) # this clause became unit
        return new_unit_clauses

def becomes_unit(clause: Clause) -> bool:
        """Checks the invariant and returns if the clause became unit or not. May change the watched literals.

        Parameters
        ----------
        clause: Clause
            The clause that maybe became unit.

        Returns
        -------
        bool
            True if the clause became unit, false otherwise.
        """

        global assignments  # we need to know about the current assignments
        # check if invariant is maintained:
        # check if at least one watched literal is true
        for literal in clause.watched_literals:
            if assignments.value(literal) == True:
                return False    # invariant holds -> clause did not become unit
        # check if both watched literals are unassigned
        both_unassigned = True
        for literal in clause.watched_literals:
            if assignments.value(literal) != None:
                both_unassigned = False
        if both_unassigned:
            return False    # invariant holds -> clause did not become unit
        # find out which of the 2 watched literals was falsified
        for literal in clause.watched_literals:
            if assignments.value(literal) == False:
                falsified_literal = literal
        watched_literal_index = clause.watched_literals.index(falsified_literal)  # is it the first or the second watched literal?
        # find a new unassigned literal to watch as our currently watched literal is falsified
        # we start looking just after the one that we currently watch and go one full loop around the whole clause
        offset = clause.literals.index(falsified_literal) + 1 # index of the falsified literal in the clause + 1
        for literal in clause.literals_iter(offset):
            if literal not in clause.watched_literals and assignments[abs(literal)] != False: # we found an unassigned (or satisfied) literal that is not already being watched
                clause.watched_literals[watched_literal_index] = literal  # so we can watch it
                return False    # that means invariant is maintained and clause not unit
        # if we didn't find an unassigned (or satisfied), unwatched literal, the invariant is broken and the clause became unit
        return True

clause = Clause([1, 2, 3, -4, -5, 6, -7])
formula = [clause]
assignments = Assignments(7)
watched_clauses = WatchedClauses(formula, 7)
def assign(assignment: Assignment):
    global assignments, watched_clauses
    assignments.assign(assignment)
    unit_clauses = get_new_unit_clauses(assignment)
    print(assignment, unit_clauses)

assign(Assignment((1, False)))
assign(Assignment((2, False)))
assign(Assignment((3, False)))
assign(Assignment((4, True)))
assign(Assignment((5, True)))
assign(Assignment((6, False)))