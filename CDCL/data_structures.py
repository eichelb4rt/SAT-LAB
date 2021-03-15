from typing import List, Tuple, Optional
from collections.abc import Sequence, Collection
import constants

def negate(boolean: Optional[bool]):
    """Negates the given extended boolean (None stays None).
    This is important as normal negation in python (not boolean) turns None into True.
    The negation of an unassigned literal would therefore be True, we do not want that.

    Parameters
    ----------
    boolean : Optional[bool]
        The given boolean.
    """

    if boolean is None:
        return None
    return not boolean

class Clause(Sequence):
    def __init__(self, literals: List[int]):
        self.literals = list(dict.fromkeys(literals))   # same list as literals, just removes duplicates
        self.watched_literals = self.literals[:2]  # watch the first 2 literals in the clause - only 1 wide if the clause is already unit
    
    def literals_iter(self, offset: int):
        """Iterate over the literals with a given index offset modulo the clause length (one full loop around the clause).

        Parameters
        ----------
        offset : int
            The given index offset.
        """

        for index in range(len(self.literals)):
            yield self.literals[(offset + index) % len(self.literals)]
    
    def __iter__(self):
        return iter(self.literals)
    
    def __getitem__(self, key: int):
        return self.literals[key]
    
    def __len__(self):
        return len(self.literals)
    
    def __str__(self):
        return str(self.literals)

class Formula:
    """The formula is a conjuction of clauses. It can be divided into orginial clauses and learned clause.
    """

    def __init__(self, clauses: List[Clause]):
        self.original_clauses = clauses
        self.learned_clauses = []
    
    def __iter__(self):
        return iter(self.original_clauses + self.learned_clauses)
    
    def learn(self, clause: Clause):
        self.learned_clauses.append(clause)

class Assignment:
    """Single variable assignment.
    """

    def __init__(self, assignment: Tuple[int, Optional[bool]], decision_level: int):
        """Creates an assignment.

        Parameters
        ----------
        assignment : Tuple[int, Optional[bool]]
            The actual assignment - the variable and the value assigned.
        decision_level : int
            The decision level at which the assignment is applied.
        """
        
        self.var = assignment[0]
        self.value = assignment[1]
        self.decision_level = decision_level
    
    def __str__(self):
        return str((self.var, self.value))

class Assignments(Sequence):
    """Partial assignment with fast access times.
    """

    def __init__(self, n: int):
        """Generates a partial assignment for a formula with n variables.

        Parameters
        ----------
        n : int
            Number of variables to be assigned.
        """

        self.values = [None] * n  # generate 'unassigned' for every variable.
        self.decision_levels = [None] * n   # generate 'no decision level yet' for every variable.
        self.reasons = [None] * n   # generate 'no reason clause' for every variable
        self.last_assignments = [None] * n    # this is for the decision heuristic. This stays even if we unassign variables.
        # Note that the value for every variable x is stored in self.assignments[x-1] since the variables start at 1 and the array starts/list starts at 0.
    
    @property
    def assignment_view(self) -> List[Assignment]:
        """Generates a view of the array in form of assignments (see class Assignment).

        Returns
        -------
        List[Assignment]
            The assignment view.
        """

        # for every index: return an assignment with variable i+1, its value stored in self.values, and its decision level stored in self.decision_levels
        return [Assignment((i + 1, self.values[i]), self.decision_levels[i]) for i in range(len(self.values))] # every index holds the value of the variable (index + 1). Now it is brought into a form that fits the class Assignment
        # variable (n) is stored at index (n-1)
    
    def __getitem__(self, variable: int) -> bool:
        """Gets the assignment for a given variable.

        Parameters
        ----------
        variable : int
            The given variable.

        Returns
        -------
        bool
            The assignment of the given variable.
        """

        return self.values[variable - 1]   # variable (n) is stored at index (n-1)
    
    def __setitem__(self, variable: int, value: Optional[bool]):
        """Sets assigns a given value to a given variable.

        Parameters
        ----------
        variable : int
            The given variable.
        value : Optional[bool]
            The given value.
        """

        self.values[variable - 1] = value  # variable (n) is stored at index (n-1)
    
    def value(self, literal: int) -> Optional[bool]:
        """Returns the value of a given literal in the current assignment.

        Parameters
        ----------
        literal : int
            The given literal.

        Returns
        -------
        Optional[bool]
            True if the literal is satisfied, False if the literal is falsified, None if the variable is not assigned.
        """

        if literal > 0:
            return self[literal]
        else:
            return negate(self[-literal])
    
    def decision_level(self, variable: int) -> Optional[int]:
        """Returns the decision level of the assignment of a given variable.

        Parameters
        ----------
        variable : int
            The given variable.

        Returns
        -------
        Optional[int]
            The decision level of the variable, None if it's unassigned.
        """

        return self.decision_levels[variable - 1]   # variable (n) is stored at index (n-1)
    
    def reason(self, variable: int) -> Optional[Clause]:
        """Returns the reason of the assignment for a given variable.

        Parameters
        ----------
        variable : int
            The given variable.

        Returns
        -------
        Optional[Clause]
            The reason for the assignment of the variable. None if unassigned or decision.
        """

        return self.reasons[variable - 1]   # variable (n) is stored at index (n-1)
    
    def last_assignment(self, variable: int) -> Optional[bool]:
        """Returns the last value that the variable was assigned.

        Parameters
        ----------
        variable : int
            The given variable.

        Returns
        -------
        Optional[bool]
            The last value that the variable was assigned.
        """

        return self.last_assignments[variable - 1]  # variable (n) is stored at index (n-1)
    
    def assign(self, assignment: Assignment, reason: Clause = None):
        """Applies a given assignment.

        Parameters
        ----------
        assignment : Assignment
            The given assignment.
        reason : Clause, optional
            The reason for the given assignment, by default None    (for decisions)
        """

        self.values[assignment.var - 1] = assignment.value # variable (n) is stored at index (n-1)
        self.last_assignments[assignment.var - 1] = assignment.value # update last assignment
        self.decision_levels[assignment.var - 1] = assignment.decision_level
        self.reasons[assignment.var - 1] = reason
    
    def __delitem__(self, variable: int):
        """Unassigns a given variable.

        Parameters
        ----------
        variable : int
            The given variable.
        """

        self.values[variable - 1] = None   # see note in __init__
        self.decision_levels[variable - 1] = None
        self.reasons[variable - 1] = None
    
    def __iter__(self):
        """Returns iterator over assignment view (See method assignment_view).
        """
        
        return iter(self.assignment_view)
    
    def __len__(self):
        return len(self.values)
    
    def __str__(self) -> str:
        """String representation of the assignments.

        Returns
        -------
        str
            The string representation.
        """

        return str([str(assignment) for assignment in self.assignment_view])

class Propagation:
    """A propagated assignment. Includes the assignment itself and a reason clause.
    """

    def __init__(self, assignment: Assignment, reason: Clause):
        self.assignment = assignment
        self.reason = reason

class DecisionLevel:
    """Sequence of assignments made on a specific decision level. Includes a decision assignment and a number of propagations. Propagations consist of an assignment and a clause for a reason.
    """

    def __init__(self, decision: Assignment):
        self.decision = decision
        self.propagations = []
    
    def add_propagation(self, assignment: Assignment, reason: Clause):
        self.propagations.append(Propagation(assignment, reason))
    
    @property
    def assignments(self) -> List[Assignment]:
        """Returns the assignments on this decision level.

        Returns
        -------
        List[Assignment]
            The list of assignments applied on this decision level (decision + propagations).
        """

        assignments = [propagation.assignment for propagation in self.propagations]    # propagation is of type (assignment, clause)
        if not self.decision is None:
            assignments.append(self.decision)
        return assignments
    
    def get_latest_assignment(self) -> Assignment:
        """Gets the latest assignment applied on this decision level.

        Returns
        -------
        Assignment
            The latest applied assignment.
        """

        # if there are no propagations, it's the decision
        if len(self.propagations) == 0:
            return self.decision
        # get the last propagation
        propagation = self.propagations[len(self.propagations) - 1]
        return propagation.assignment

class Trail(Sequence):
    """A trail of the decisions. Is divided into decision levels.
    """

    def __init__(self):
        self.trail: List[DecisionLevel] = []
        self.trail.append(DecisionLevel(None))  # decision level 0
    
    @property
    def decision_level(self) -> int:
        """Returns current decision level.

        Returns
        -------
        int
            The current decision level.
        """

        return len(self.trail) - 1  # the decision level is the amount of decision levels n = len(0,1,...,n) - 1
    
    def __len__(self):
        return len(self.trail)
    
    def __getitem__(self, key: int) -> DecisionLevel:
        return self.trail[key]
    
    def decide(self, assignment: Assignment):
        self.trail.append(DecisionLevel(assignment))    # create a new decision level with the decision
    
    def add_propagation(self, assignment: Assignment, reason: Clause):
        """Adds a propagation to the propagation side of the latest decision level.

        Parameters
        ----------
        assignment : Assignment
            The assignment that was propagated.
        reason : Clause
            The reason clause for the propagated assignment.
        """

        self.trail[self.decision_level].add_propagation(assignment, reason)
    
    def backtrack(self, level: int):
        """Backtracking to the given level.

        Parameters
        ----------
        level : int
            The given level.
        """

        self.trail = self.trail[:level + 1] # keeps every decision level before level, removes everything else
        self.trail[level].propagations = [] # keep only the decision on the level that we backtracked to

class VSIDS:
    """Class that manages VSIDS variable selection.
    """

    def __init__(self, n: int):
        """Initiates the VSIDS data structure for variable selection.

        Parameters
        ----------
        n : int
            The number of variables.
        """

        self.b = 1.0  # instead of multiplying all counters with c after a while, we'll just divide b by c and add it to the counter all the time instead of 1 (MiniSat approach)
        self.counters = [0.0] * n   # note that every variable (x) is stored at index (x - 1)
        self.conflicts = 0  # number of conflicts
        # we could now sort a list of variables we want to assign next, but i'm too lazy
    
    def touch(self, variable: int):
        """To be called when a variable is 'touched' in a conflict.

        Parameters
        ----------
        variable : int
            The touched variable.
        """

        self.counters[variable] -=- self.b  # way cooler than +=, fancy schmancy time
    
    def conflict(self):
        """Increment the conflict counter.
        """

        self.conflicts -=- 1    # chad town
        # if we reached the max number of conflicts, we crank that boi up
        if self.conflicts >= constants.VSIDS_CONFLICTS_UNTIL_DECAY:
            self.b /= constants.VSIDS_DECAY
            self.conflicts = 0
        # if our b has reached a limit where we might fear overflows (probably not 2**10, but better safe than sorry), we scale the whole thing
        if self.b >= 2**10:
            for index, counter in enumerate(self.counters):
                self.counter[index] = counter / self.b
                self.b = 1