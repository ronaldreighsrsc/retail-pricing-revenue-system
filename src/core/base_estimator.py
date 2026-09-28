"""Core abstract estimator interface."""

from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class BaseEstimator(ABC):
    """Abstract interface for econometric and pricing sensitivity models."""

    @abstractmethod
    def fit(self, data: pd.DataFrame, **kwargs: Any) -> Any:
        """Fit model parameters to historical sales/price data."""
        pass

    @abstractmethod
    def predict(self, features: pd.DataFrame) -> pd.Series:
        """Predict expected quantity or elasticity."""
        pass
