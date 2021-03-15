from typing import List, Tuple, Optional
from collections import deque
from data_structures import Formula, Clause, Assignments, Assignment, Trail, VSIDS
import cdcl
import random

# global variables
a = [
    [-1, -2, -3], 
    [-1, 2, -3], 
    [1, -2, -3], 
    [1, 2, -3], 
    [-1, -2, 3], 
    [-1, 2, 3], 
    [1, -2, 3], 
    [1, 2, 3]
]
b = [ 
    [-1, 2, -3], 
    [1, -2, -3], 
    [1, 2, -3], 
    [-1, -2, 3], 
    [-1, 2, 3], 
    [1, -2, 3], 
    [1, 2, 3]
]
c = [
    [1], 
    [-1, 2],
    [-1, -2]
]
for clauses_array_form in [a, b, c]:
    cdcl.assignments = Assignments(4)
    cdcl.vsids = VSIDS(4)
    cdcl.original_formula = Formula([Clause(literals) for literals in clauses_array_form])
    cdcl.trail = Trail()
    cdcl.STATS.start()
    print(cdcl.cdcl_solver())
    cdcl.STATS.stop()
    print(cdcl.STATS)