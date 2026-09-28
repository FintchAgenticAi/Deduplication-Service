from abc import ABC, abstractmethod


class BaseDedupRule(ABC):

    @abstractmethod
    def apply(self, record1, record2):
        """
        Compare two records and determine whether they are duplicates.
        """
        pass