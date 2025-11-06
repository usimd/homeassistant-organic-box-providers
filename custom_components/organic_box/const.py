"""Constants for the Organic Box integration."""

from typing import Final

DOMAIN: Final = "organic_box"

# Configuration and options
CONF_PROVIDER: Final = "provider"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SHOP_ID: Final = "shop_id"

# Providers
PROVIDER_OEKOBOX: Final = "oekobox"

# Update intervals
DEFAULT_SCAN_INTERVAL: Final = 900  # 15 minutes in seconds

# Attributes
ATTR_NEXT_DELIVERY: Final = "next_delivery"
ATTR_BASKET_ITEMS: Final = "basket_items"
ATTR_PROVIDER: Final = "provider"
