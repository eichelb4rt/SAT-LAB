#!/bin/python3
# SHEBANG

import os
from solvers import solvers

cnfs_folder = "../random-cnf/out/"
files = os.listdir(cnfs_folder)
for solver in solvers:
    print("================================================================")
    print(solver.name)
    print("================================================================")
    for file in files:
        path = cnfs_folder + file
        print("================================")
        print(path)
        print("================================")
        print(solver.solve(path))
        print(solver.stats_run)