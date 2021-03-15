from abc import ABC, abstractmethod
import sys, os
# add the global lib directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}CDCL")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}2-SAT")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}DPLL")
from stats import CDCLStats, DPLLStats, TwoSatStats, StatsAgent, SolverStats
import cdcl
import dpll_mf
import two_sat

class Solver(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the solver.

        Returns
        -------
        str
            Name of the solver. Can be different for different configs.
        """

    @abstractmethod
    def solve(self, input: str) -> bool:
        """Solves SAT for a given CNF in Dimacs.

        Parameters
        ----------
        input : str
            The file that the dimacs cnf is stored in.

        Returns
        -------
        bool
            True if cnf is satisfiable, False otherwise.
        """
    
    @property
    @abstractmethod
    def stats(self) -> SolverStats:
        """Returns the StatsAgent for the stats.

        Returns
        -------
        StatsAgent
            The StatsAgent.
        """

class CDCLSolver:
    @property
    def name(self) -> str:
        return "CDCL"

    def solve(self, input: str) -> bool:
        return cdcl.solve_input(input)
    
    @property
    def stats(self) -> CDCLStats:
        return cdcl.STATS

class DPLLMFSolver:
    @property
    def name(self) -> str:
        return "DPLL memory-friendly"

    def solve(self, input: str) -> bool:
        return dpll_mf.solve_input(input)
    
    @property
    def stats(self) -> DPLLStats:
        return dpll_mf.STATS

class TwoSatSolver:
    @property
    def name(self) -> str:
        return "2-SAT"

    def solve(self, input: str) -> bool:
        return two_sat.solve_input(input)
    
    @property
    def stats(self) -> TwoSatStats:
        return two_sat.STATS

input = "../random-cnf/out/random_cnf_0.txt"
solvers = [DPLLMFSolver(), CDCLSolver(), TwoSatSolver()]
for solver in solvers:
    print("================================================================")
    print(solver.name)
    print("================================================================")
    print(solver.solve(input))
    print(solver.stats)