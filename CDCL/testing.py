from typing import List, Tuple, Optional
from copy import deepcopy, copy
from collections.abc import Sequence, Collection, MutableSequence
from data_structures import Formula, Clause, Assignments, Assignment, Trail, VSIDS
import cdcl

# global variables
clauses_array_form = [[-1, -2, -3], [-1, 2, -3], [1, -2, -3], [1, 2, -3], [-1, -2, 3], [-1, 2, 3], [1, -2, 3], [1, 2, 3]]
cdcl.assignments = Assignments(4)
cdcl.vsids = VSIDS(4)
cdcl.original_formula = Formula([Clause(literals) for literals in clauses_array_form])
cdcl.trail = Trail()

assignment = Assignment((1, True), 0)
print(assignment)