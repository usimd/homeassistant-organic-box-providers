
# Organic Box Home Assistant Integration

<p align="center">
	<img src="https://raw.githubusercontent.com/usimd/homeassistant-organic-box-addon/main/custom_components/organic_box/icon.png" width="128" alt="Organic Box Icon"/>
</p>

This custom integration enables Home Assistant to query various organic food box delivery services for their next scheduled delivery and planned basket contents. It is designed with a plugin architecture, making it easy to add new providers.

## Features
- Supports multiple organic box providers (OekoBox Online included, more can be added)
- Abstract provider base class for easy extension
- Periodically updates next delivery and basket contents
- Exposes sensor entities for:
  - Next delivery date
  - Basket items count (with detailed items list in attributes)
- Dynamic configuration UI (config flow)
  - Select provider from dropdown
  - Configure provider-specific credentials
- Data update coordinator for efficient polling
- Service to manually update basket/delivery

## Installation via HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=usimd&repository=homeassistant-organic-box-providers&category=integration)


1. Go to HACS > Integrations > Custom Repositories.
2. Add this repository URL: `https://github.com/usimd/homeassistant-organic-box-providers` as a "Integration".
3. Install "Organic Box" from HACS.
4. Restart Home Assistant.
5. Add the integration via the UI ("Add Integration" > "Organic Box").
6. Select your provider from the dropdown.
7. Enter your credentials (username and password).
8. **For OekoBox Online**: Select your shop from the dropdown list.

## Manual Installation
1. Copy the `organic_box` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the UI ("Add Integration" > "Organic Box").
4. Select your provider from the dropdown.
5. Enter your credentials (username and password).
6. **For OekoBox Online**: Select your shop from the dropdown list.

## Configuration Flow

The integration uses a multi-step configuration flow:

### Step 1: Provider Selection
Choose your organic box provider from the dropdown menu.

### Step 2: Credentials
Enter your username and password for the selected provider.

### Step 3: Shop Selection (OekoBox Online only)
For OekoBox Online, you'll be presented with a list of shops associated with your account. Select the shop you want to track deliveries for.

## Supported Providers
- **OekoBox Online** - Uses the `pyoekoboxonline` library
  - Requires username, password, and shop selection

## Configuration

Configuration is done entirely through the UI:
1. Go to Settings > Devices & Services
2. Click "Add Integration"
3. Search for "Organic Box"
4. Select your provider from the dropdown
5. Enter your credentials

## Adding New Providers

To add support for a new organic box provider:

1. **Create a new provider class** in a new file (e.g., `custom_components/organic_box/newprovider.py`):
   ```python
   from .provider import OrganicBoxProvider
   from .models import DeliveryInfo, BasketItem
   
   class NewProvider(OrganicBoxProvider):
       @property
       def name(self) -> str:
           return "New Provider Name"
       
       async def authenticate(self) -> bool:
           # Implement authentication logic
           pass
       
       async def get_next_delivery(self) -> DeliveryInfo:
           # Implement data fetching logic
           pass
       
       async def test_connection(self) -> bool:
           # Implement connection test
           pass
       
       async def close(self) -> None:
           # Clean up resources
           pass
   ```

2. **Register the provider** in `const.py`:
   ```python
   PROVIDER_NEWPROVIDER: Final = "newprovider"
   ```

3. **Add it to the config flow** in `config_flow.py`:
   - Add the provider to the `PROVIDERS` dictionary
   - Add provider instantiation in the `_test_credentials` method

4. **Update `__init__.py`** to handle the new provider:
   - Import the new provider class
   - Add a case in `async_setup_entry` to instantiate it

5. **Add the dependency** to `manifest.json` if needed:
   ```json
   "requirements": ["pyoekoboxonline", "your-new-library"]
   ```

## Services
- `organic_box.update_basket`: Manually trigger an update of basket/delivery data.

## Sensors

The integration provides two sensors per configured account:

1. **Next Delivery Sensor** (`sensor.organic_box_next_delivery`)
   - State: The next delivery date and time
   - Attributes: Provider name, total items count

2. **Basket Items Sensor** (`sensor.organic_box_basket_items`)
   - State: Number of items in the basket
   - Attributes: Provider name, detailed list of items with names, quantities, and units

## Architecture

The integration follows Home Assistant best practices:

- **Abstract Provider Base Class**: All providers inherit from `OrganicBoxProvider` 
- **Data Models**: Clean data structures (`DeliveryInfo`, `BasketItem`)
- **Config Flow**: UI-based configuration with provider selection
- **Data Update Coordinator**: Efficient polling with configurable intervals
- **Proper Error Handling**: Graceful handling of authentication and API errors
- **Type Hints**: Full type annotation for better code quality

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Organic Box Integration                    │ │
│  │                                                          │ │
│  │  ┌─────────────────┐      ┌──────────────────────┐    │ │
│  │  │  Config Flow    │      │  Data Coordinator    │    │ │
│  │  │  (UI Setup)     │      │  (Periodic Updates)  │    │ │
│  │  └─────────────────┘      └──────────────────────┘    │ │
│  │           │                         │                   │ │
│  │           ▼                         ▼                   │ │
│  │  ┌──────────────────────────────────────────────┐     │ │
│  │  │      OrganicBoxProvider (Abstract)           │     │ │
│  │  │  • authenticate()                            │     │ │
│  │  │  • get_next_delivery() → DeliveryInfo       │     │ │
│  │  │  • test_connection()                         │     │ │
│  │  │  • close()                                   │     │ │
│  │  └──────────────────────────────────────────────┘     │ │
│  │           │                                             │ │
│  │           ├─────────────┬──────────────┐               │ │
│  │           ▼             ▼              ▼               │ │
│  │  ┌──────────────┐ ┌──────────┐ ┌────────────┐        │ │
│  │  │   OekoBox    │ │ Provider │ │  Provider  │        │ │
│  │  │   Provider   │ │    2     │ │     3      │        │ │
│  │  └──────────────┘ └──────────┘ └────────────┘        │ │
│  │           │                                             │ │
│  │           ▼                                             │ │
│  │  ┌──────────────────────────────────────────────┐     │ │
│  │  │           Sensor Entities                    │     │ │
│  │  │  • Next Delivery Sensor                     │     │ │
│  │  │  • Basket Items Sensor                      │     │ │
│  │  └──────────────────────────────────────────────┘     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                       │                    │
         ▼                       ▼                    ▼
   ┌──────────┐          ┌──────────┐         ┌──────────┐
   │ OekoBox  │          │ Provider │         │ Provider │
   │   API    │          │  API 2   │         │  API 3   │
   └──────────┘          └──────────┘         └──────────┘
```

## Development

To set up the development environment:

```bash
# Install Home Assistant core for development
pip install homeassistant

# Install the integration dependencies
pip install -r requirements.txt
```

## To Do
- [ ] Add more providers (contributions welcome!)
- [ ] Add service to align basket with Home Assistant shopping list
- [ ] Add tests
- [ ] Add support for multiple deliveries
- [ ] Add configuration option for update interval

## License
MIT
