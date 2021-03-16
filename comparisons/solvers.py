#!/bin/python3
# SHEBANG

from abc import ABC, abstractmethod
import sys, os
# add the global lib directory to the path so i can import read_dimacs and more already existing features from it
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}global_libs")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}CDCL")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}2-SAT")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}DPLL")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + f"{os.path.sep}DPLL_MF")
from stats import CDCLStats, DPLLStats, TwoSatStats, StatsAgent, SolverStats
import cdcl
import dpll
import dpll_mf
import two_sat

class Solver(ABC):

    def __init__(self):
        self.stats_overall = [] # records the stats over time
    
    def stop_time(self):
        time_passed = self.stats_run.get_measurement_by_name("Process Time").value
        if len(self.stats_overall) == 0:
            self.stats_overall.append(time_passed)
        else:
            last_time = self.stats_overall[len(self.stats_overall) - 1]
            self.stats_overall.append(time_passed + last_time)

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
    def stats_run(self) -> SolverStats:
        """Returns the StatsAgent for the stats. Note that it only carries the stats after 1 run.

        Returns
        -------
        StatsAgent
            The StatsAgent.
        """

class CDCLSolver(Solver):
    @property
    def name(self) -> str:
        return "CDCL"

    def solve(self, input: str) -> bool:
        return cdcl.solve_input(input)
    
    @property
    def stats_run(self) -> CDCLStats:
        return cdcl.STATS

class DPLLMFSolver(Solver):
    @property
    def name(self) -> str:
        return "DPLL memory-friendly"

    def solve(self, input: str) -> bool:
        return dpll_mf.solve_input(input)
    
    @property
    def stats_run(self) -> DPLLStats:
        return dpll_mf.STATS

class DPLLSolver(Solver):
    @property
    def name(self) -> str:
        return "DPLL recursive"

    def solve(self, input: str) -> bool:
        return dpll.solve_input(input)
    
    @property
    def stats_run(self) -> DPLLStats:
        return dpll.STATS

class TwoSatSolver(Solver):
    @property
    def name(self) -> str:
        return "2-SAT"

    def solve(self, input: str) -> bool:
        return two_sat.solve_input(input)
    
    @property
    def stats_run(self) -> TwoSatStats:
        return two_sat.STATS

solvers = [CDCLSolver()]