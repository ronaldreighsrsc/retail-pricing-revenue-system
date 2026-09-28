"""Core abstract repository interface."""

from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseRepository(ABC):
    """Abstract interface for retail pricing data access."""

    @abstractmethod
    def get_products(self) -> pd.DataFrame:
        """Fetch all product dimensions."""
        pass

    @abstractmethod
    def get_transactions(self, sku: Optional[str] = None, country_id: Optional[str] = None) -> pd.DataFrame:
        """Fetch transaction facts."""
        pass

    @abstractmethod
    def get_competitor_quotes(self, sku: Optional[str] = None) -> pd.DataFrame:
        """Fetch competitor pricing benchmark facts."""
        pass
