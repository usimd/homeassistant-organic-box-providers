"""Abstract base class for organic box providers."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .models import DeliveryInfo

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class OrganicBoxProvider(ABC):
    """Abstract base class for organic box providers."""

    def __init__(self, hass: "HomeAssistant", username: str, password: str) -> None:
        """Initialize the provider.

        Args:
            hass: Home Assistant instance
            username: The username for authentication
            password: The password for authentication
        """
        self._hass = hass
        self._username = username
        self._password = password
        self._authenticated = False

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the provider.

        Returns:
            True if authentication was successful, False otherwise
        """

    @abstractmethod
    async def get_next_delivery(self) -> DeliveryInfo:
        """Get information about the next delivery.

        Returns:
            DeliveryInfo object containing delivery date and items
        """

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the provider.

        Returns:
            True if connection test was successful, False otherwise
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""

    @property
    def is_authenticated(self) -> bool:
        """Return whether the provider is authenticated."""
        return self._authenticated

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""

    async def pause_next_delivery(self) -> bool:
        """Pause the next delivery.

        Returns:
            True if successful, False otherwise

        Note:
            Default implementation returns False (not supported).
            Override this method in provider implementations that support pausing.
        """
        return False

    async def unpause_next_delivery(self) -> bool:
        """Unpause (resume) the next delivery.

        Returns:
            True if successful, False otherwise

        Note:
            Default implementation returns False (not supported).
            Override this method in provider implementations that support pausing.
        """
        return False

    def supports_pause(self) -> bool:
        """Return whether the provider supports pausing deliveries.

        Returns:
            True if the provider supports pausing, False otherwise

        Note:
            Default implementation returns False.
            Override this method in provider implementations that support pausing.
        """
        return False
