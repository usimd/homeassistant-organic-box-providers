# Organic Box Home Assistant Integration

This custom integration enables Home Assistant to query various organic food box delivery services for their next scheduled delivery and planned basket contents. It is designed with a plugin architecture, making it easy to add new providers.

## Features
- Supports multiple organic box providers (Amperhof included, more can be added)
- Periodically updates next delivery and basket contents
- Exposes entities for next delivery date and planned basket
- Dynamic configuration UI (config flow)
- Service to manually update basket/delivery
- Optional: Align planned basket with Home Assistant's To Do list (shopping list)

## Installation
1. Copy the `organic_box` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the UI ("Add Integration" > "Organic Box").
4. Select your provider and enter required credentials (JWT token for Amperhof).

## Configuration Example
```yaml
organic_box:
  amperhof:
    jwt_token: "your_jwt_token_here"
```

## Adding Providers
- Implement a new provider class in `provider.py` (subclass `OrganicBoxProvider`).
- Add provider-specific config options in the config flow.
- Register the provider in the integration.

## Services
- `organic_box.update_basket`: Manually trigger an update of basket/delivery data.
- `organic_box.align_shopping_list`: Remove items from Home Assistant's To Do list that are present in the planned basket.

## To Do
- [ ] Add more providers
- [ ] Polish config flow UI
- [ ] Add tests

## License
MIT
