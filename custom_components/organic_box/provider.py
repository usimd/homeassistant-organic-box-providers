from typing import Dict, Any
from .models import Delivery

class OrganicBoxProvider:
    """Abstract base class for organic box providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def async_get_next_delivery(self) -> Delivery:
        """Return the next scheduled delivery."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Provider name."""
        raise NotImplementedError
