from typing import List, Tuple, Optional
from collections.abc import Sequence, Collection

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
        self.literals = literals
        self.watched_literals = literals[:2]  # watch the first 2 literals in the clause - only 1 wide if the clause is already unit
    
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

class Formula: List[Clause]

class Assignment(Tuple[int, Optional[bool]]):
    """Single variable assignment.
    """

    @property
    def var(self) -> int:
        """The assigned variable.

        Returns
        -------
        int
            The assigned variable.
        """

        return self[0]
    
    @property
    def value(self) -> Optional[bool]:
        """The assigned value.

        Returns
        -------
        Optional[bool]
            The assigned value.
        """

        return self[1]

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

        self.assignments = [None] * n  # generate 'unassigned' for every variable.
        # Note that the value for every variable x is stored in self.assignments[x-1] since the variables start at 1 and the array starts/list starts at 0.
    
    @property
    def assignment_view(self) -> List[Assignment]:
        """Generates a view of the array in form of assignments (see class Assignment).

        Returns
        -------
        List[Assignment]
            The assignment view.
        """

        return [(index + 1, value) for index, value in enumerate(self.assignments)] # every index holds the value of the variable (index + 1). Now it is brought into a form that fits the class Assignment
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

        return self.assignments[variable - 1]   # variable (n) is stored at index (n-1)
    
    def __setitem__(self, variable: int, value: Optional[bool]):
        """Sets assigns a given value to a given variable.

        Parameters
        ----------
        variable : int
            The given variable.
        value : Optional[bool]
            The given value.
        """

        self.assignments[variable - 1] = value  # variable (n) is stored at index (n-1)
    
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
    
    def assign(self, assignment: Assignment):
        """Applies a given assignment.

        Parameters
        ----------
        assignment : Assignment
            The given assignment.
        """

        self.assignments[assignment.var - 1] = assignment.value # variable (n) is stored at index (n-1)
    
    def __delitem__(self, variable: int):
        """Unassigns a given variable.

        Parameters
        ----------
        variable : int
            The given variable.
        """

        self.assignments[variable - 1] = None   # see note in __init__
    
    def __iter__(self):
        """Returns iterator over assignment view (See method assignment_view).
        """
        
        return iter(self.assignment_view)
    
    def __len__(self):
        return len(self.assignments)
    
    def __str__(self) -> str:
        """String representation of the assignments.

        Returns
        -------
        str
            The string representation.
        """

        return str(self.assignment_view)

class DecisionLevel:
    """Sequence of assignments made on a specific decision level. Includes a decision assignment and a number of propagations. Propagations consist of an assignment and a clause for a reason.
    """

    def __init__(self, decision: Assignment):
        self.decision = decision
        self.propagations = []  # elements of type (assignment, reason)
    
    def add_propagation(self, assignment: Assignment, reason: Clause):
        self.propagations.append((assignment, reason))

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