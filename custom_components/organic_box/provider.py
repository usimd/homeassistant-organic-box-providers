"""Provider base class for Organic Box integration."""

from typing import Any

from .models import Delivery


class OrganicBoxProvider:
    """Abstract base class for organic box providers."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize provider with config."""
        self.config = config

    async def async_get_next_delivery(self) -> Delivery:
        """Return the next scheduled delivery."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        """Provider name."""
        raise NotImplementedError
