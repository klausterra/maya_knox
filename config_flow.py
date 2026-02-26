import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector

DOMAIN = "maya_knox"

class MayaKnoxOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data=user_input)
        opcoes = self._entry.options or self._entry.data
        return self.async_show_form(step_id="init", data_schema=self._get_schema(opcoes))

    def _get_schema(self, defaults):
        return vol.Schema({
            vol.Required("sensores_perimetro", default=defaults.get("sensores_perimetro", [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "camera"])),
            vol.Required("sensores_internos", default=defaults.get("sensores_internos", [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="binary_sensor")),
            vol.Optional("sensor_campainha", default=defaults.get("sensor_campainha", [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "sensor"])),
            vol.Required("sirene", default=defaults.get("sirene", [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["switch", "siren", "light"])),
            vol.Required("moradores", default=defaults.get("moradores", [])): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="person")),
            vol.Optional("notify_service_name", default=defaults.get("notify_service_name", "notify.notify")): selector.TextSelector(),
            vol.Optional("alexa_notify_service", default=defaults.get("alexa_notify_service", "")): selector.TextSelector(),
            vol.Optional("alexa_msg_campainha", default=defaults.get("alexa_msg_campainha", "Atenção, campainha acionada.")): str,
            vol.Optional("alexa_msg_alarme", default=defaults.get("alexa_msg_alarme", "Atenção, o alarme foi disparado! {msg}")): str,
            vol.Optional("ativar_auto_armar", default=defaults.get("ativar_auto_armar", True)): selector.BooleanSelector()
        })

class MayaKnoxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    @staticmethod
    @callback
    def async_get_options_flow(config_entry): return MayaKnoxOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if self._async_current_entries(): return self.async_abort(reason="single_instance_allowed")
        if user_input is not None: return self.async_create_entry(title="Central Maya Knox", data=user_input)
        return self.async_show_form(step_id="user", data_schema=MayaKnoxOptionsFlowHandler(None)._get_schema({}))