from abc import ABC, abstractmethod
from typing import Optional
import time, tracemalloc

class Measurement(ABC):
    """Class for measuring stuff.
    """

    @abstractmethod
    def start(self):
        """Start the measurement.
        """
        pass

    @abstractmethod
    def stop(self):
        """Stop the measurement.
        """
        pass

    @property
    @abstractmethod
    def value(self):
        """The value of the measurement.
        """
        pass

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Formatted name of the measurement.

        Returns
        -------
        str
            The formatted name.
        """
        pass

    @property
    @abstractmethod
    def format_value(self) -> str:
        """The formatted value of the measurement.

        Returns
        -------
        str
            The formatted value.
        """
        pass

class MeasureTime(Measurement):
    """Measures time.
    """

    def start(self):
        self.start_time = time.process_time()
    
    def stop(self):
        self.time_elapsed = time.process_time() - self.start_time
    
    @property
    def value(self) -> Optional[float]:
        if self.time_elapsed:
            return self.time_elapsed
        return None
    
    @property
    def format_name(self) -> str:
        return "Process Time"
    
    @property
    def format_value(self) -> str:
        if self.value:
            return f"{round(self.value, 2)} s"
        return ""

class PeakMemory(Measurement):
    """Measures peak memory usage.
    """

    def start(self):
        tracemalloc.start()
    
    def stop(self):
        self.current_memory, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    
    @property
    def value(self) -> Optional[float]:
        if self.peak_memory:
            return self.peak_memory
        return None
    
    @property
    def format_name(self) -> str:
        return "Peak Memory Usage"
    
    @property
    def format_value(self) -> str:
        if self.value:
            return f"{round(self.value / 10**6, 2)} MB"
        return ""

class Counter(Measurement):
    """Used for counting things.
    """

    def __init__(self):
        """Init so we don't have to worry about self.count not exisiting.
        """

        self.count = 0

    def start(self):
        self.count = 0
    
    def stop(self):
        """Stop doesn't do anything for counters.
        """
        pass

    @property
    def value(self):
        return self.count

    @property
    def format_value(self) -> str:
        return str(self.count)
    
    def increment(self):
        self.count -=- 1

class Propagations(Counter):
    @property
    def format_name(self) -> str:
        return "Number of Propagations"

class Decisions(Counter):
    @property
    def format_name(self) -> str:
        return "Number of Decisions"

class Conflicts(Counter):
    @property
    def format_name(self) -> str:
        return "Number of Conflicts"

class LearnedClauses(Counter):
    @property
    def format_name(self) -> str:
        return "Number of Learned Clauses"

class Restarts(Counter):
    @property
    def format_name(self) -> str:
        return "Number of Restarts"