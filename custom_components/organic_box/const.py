"""Constants for the Organic Box integration."""

from typing import Final

DOMAIN: Final = "organic_box"

# Configuration and options
CONF_PROVIDER: Final = "provider"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SHOP_ID: Final = "shop_id"
CONF_ENABLE_SHOPPING_LIST_MATCH: Final = "enable_shopping_list_match"
CONF_MATCH_THRESHOLD: Final = "match_threshold"
CONF_AUTO_CANCEL_ON_PAUSE_CONFLICT: Final = "auto_cancel_on_pause_conflict"

# Providers
PROVIDER_OEKOBOX: Final = "oekobox"

# Update intervals
DEFAULT_SCAN_INTERVAL: Final = 900  # 15 minutes in seconds

# Attributes
ATTR_NEXT_DELIVERY: Final = "next_delivery"
ATTR_BASKET_ITEMS: Final = "basket_items"
ATTR_PROVIDER: Final = "provider"
ATTR_LAST_ORDER_CHANGE: Final = "last_order_change"
ATTR_MATCHED_ITEMS: Final = "matched_shopping_list_items"

# Shopping list matching
DEFAULT_MATCH_THRESHOLD: Final = 80  # 80% similarity threshold
