import os
from solvers import solvers
import matplotlib.pyplot as plt

cnfs_folder = "../random-cnf/out/"
files = os.listdir(cnfs_folder)
#for solver in solvers:
#    print("================================================================")
#    print(solver.name)
#    print("================================================================")
#    for file in files:
#        path = cnfs_folder + file
#        print("================================")
#        print(path)
#        print("================================")
#        print(solver.solve(path))
#        print(solver.stats)

for solver in solvers:
    for file in files:
        path = cnfs_folder + file
        solver.solve(path)
        solver.stop_time()
# now plot that shit
x_axis = range(len(files))
for solver in solvers:
    plt.plot(x_axis, solver.stats_overall, label = solver.name)
plt.xlabel('cnfs processed')
plt.ylabel('time in seconds')
plt.title('SAT-Solver comparison')
# show a legend on the plot
plt.legend()
# function to show the plot
plt.show()