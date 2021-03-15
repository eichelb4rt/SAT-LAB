from abc import ABC, abstractmethod
from measurements import Measurement, MeasureTime, PeakMemory, Propagations, Decisions, Conflicts, LearnedClauses, Restarts
from tabulate import tabulate
from typing import List

class StatsAgent:
    """This guy handles all the stats across the code.
    """
    
    def __init__(self, measurements: List[Measurement]):
        """Initiates the agent.

        Parameters
        ----------
        counters : List[str]
            List of the names of the counters.
        """

        self.measurements = measurements
    
    def start(self):
        """Starts all the measurements.
        """

        for measurement in self.measurements:
            measurement.start()
    
    def stop(self):
        """Ends all the measurements.
        """

        for measurement in self.measurements:
            measurement.stop()
    
    def __str__(self):
        return tabulate([[measurement.format_name, measurement.format_value] for measurement in self.measurements])

class SolverStats(StatsAgent):
    def __init__(self, extra_measurements = []):
        """Initiates agent for a generic solver.
        """

        self.propagations = Propagations()
        self.decisions = Decisions()
        super().__init__([MeasureTime(), PeakMemory(), self.propagations, self.decisions] + extra_measurements)
    
    def propagate(self):
        """Increments the number of propagations.
        """
        
        self.propagations.increment()
    
    def decide(self):
        """Increments the number of decisions.
        """

        self.decisions.increment()

class DPLLStats(SolverStats):
    pass    # literally just SolverStats

class TwoSatStats(SolverStats):
    pass    # literally just SolverStats

class CDCLStats(SolverStats):
    def __init__(self):
        """Initiates agent for dpll.
        """

        self.conflicts = Conflicts()
        self.learned_clauses = LearnedClauses()
        self.restarts = Restarts()
        super().__init__([
            self.conflicts,
            self.learned_clauses,
            self.restarts
        ])
    
    def conflict(self):
        """Increments the number of conflicts.
        """

        self.conflicts.increment()
    
    def learn(self):
        """Increments the number of learned clauses.
        """

        self.learned_clauses.increment()
    
    def restart(self):
        """Increments the number of restarts.
        """

        self.restarts.increment()