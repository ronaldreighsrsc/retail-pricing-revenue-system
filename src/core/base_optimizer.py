"""Core abstract optimizer interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseOptimizer(ABC):
    """Abstract interface for pricing and markdown optimizers."""

    @abstractmethod
    def optimize(self, **kwargs: Any) -> Any:
        """Run mathematical optimization routine."""
        pass
