import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN


PROVIDERS = {
    "amperhof": {
        "fields": {
            "username": str,
            "password": str
        },
        "label": "Amperhof (Germany)",
        "description": "Requires username and password for authentication."
    },
    # Example for another provider:
    # "otherbox": {
    #     "fields": {
    #         "username": str,
    #         "password": str
    #     },
    #     "label": "OtherBox",
    #     "description": "Requires username and password."
    # }
}

class OrganicBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            provider = user_input["provider"]
            return await self.async_step_provider({"provider": provider})
        provider_options = {k: PROVIDERS[k]["label"] for k in PROVIDERS}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("provider"): vol.In(list(provider_options.keys()))
            }),
            description_placeholders={"providers": ", ".join(provider_options.values())},
            errors=errors
        )

    async def async_step_provider(self, user_input=None):
        provider = user_input["provider"]
        fields = PROVIDERS[provider]["fields"]
        schema = vol.Schema({vol.Required(k): str for k in fields})
        if user_input is not None and all(k in user_input for k in fields):
            entry_data = {"provider": provider}
            entry_data.update({k: user_input[k] for k in fields})
            return self.async_create_entry(title=PROVIDERS[provider]["label"], data=entry_data)
        return self.async_show_form(
            step_id="provider",
            data_schema=schema,
            description_placeholders={"description": PROVIDERS[provider].get("description", "")},
            errors={}
        )
