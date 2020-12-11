from abc import ABC, abstractmethod
from measurements import Measurement, MeasureTime, PeakMemory, Propagations, Decisions, Conflicts
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

class DPLLStats(StatsAgent):
    def __init__(self):
        """Initiates agent for dpll.
        """

        self.propagations = Propagations()
        self.decisions = Decisions()
        super().__init__([MeasureTime(), PeakMemory(), self.propagations, self.decisions])
    
    def propagate(self):
        """Increments the number of propagations.
        """
        
        self.propagations.increment()
    
    def decide(self):
        """Increments the number of decisions.
        """

        self.decisions.increment()

class TwoSatStats(StatsAgent):
    def __init__(self):
        """Initiates agent for dpll.
        """

        self.propagations = Propagations()
        self.decisions = Decisions()
        super().__init__([MeasureTime(), PeakMemory(), self.propagations, self.decisions])
    
    def propagate(self):
        """Increments the number of propagations.
        """

        self.propagations.increment()
    
    def decide(self):
        """Increments the number of decisions.
        """

        self.decisions.increment()

class CDCLStats(StatsAgent):
    def __init__(self):
        """Initiates agent for dpll.
        """

        self.propagations = Propagations()
        self.decisions = Decisions()
        self.conflicts = Conflicts()
        super().__init__([MeasureTime(), PeakMemory(), self.propagations, self.decisions, self.conflicts()])
    
    def propagate(self):
        """Increments the number of propagations.
        """

        self.propagations.increment()
    
    def decide(self):
        """Increments the number of decisions.
        """

        self.decisions.increment()
    
    def add_conflict(self):
        """Increments the number of conflicts.
        """

        self.conflicts.increment()