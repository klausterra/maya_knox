import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

DOMAIN = "maya_knox"

class MayaKnoxOptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Garantir que campos múltiplos sejam listas antes de salvar
            list_keys = [
                "sensores_perimetro", "sensores_internos", "sensor_campainha", 
                "entidade_sirene_alarme", "entidade_chime_campainha", "moradores", 
                "notify_servicos_campainha", "notify_servicos_sirene", 
                "alexa_notify_servicos_campainha", "alexa_notify_servicos_alarme",
                "rastreadores_omada", "alexa_campainha_som_dispositivos"
            ]
            for key in list_keys:
                if key in user_input:
                    user_input[key] = cv.ensure_list(user_input[key])
            return self.async_create_entry(title="", data=user_input)
        
        opcoes = self._entry.options or self._entry.data
        return self.async_show_form(step_id="init", data_schema=self._get_schema(opcoes))

    def _get_schema(self, defaults):
        notify_opts = []
        if hasattr(self, 'hass') and self.hass:
            services = self.hass.services.async_services().get("notify", {})
            notify_opts = [{"value": f"notify.{s}", "label": f"notify.{s}"} for s in services]

        def _ensure_list(val):
            if val is None: return []
            return [val] if isinstance(val, str) else val

        notify_selector = selector.SelectSelector(selector.SelectSelectorConfig(
            options=notify_opts,
            custom_value=True,
            multiple=True,
            mode=selector.SelectSelectorMode.DROPDOWN
        ))

        return vol.Schema({
            vol.Required("sensores_perimetro", default=_ensure_list(defaults.get("sensores_perimetro", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "camera"])),
            vol.Required("sensores_internos", default=_ensure_list(defaults.get("sensores_internos", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="binary_sensor")),
            vol.Optional("sensor_campainha", default=_ensure_list(defaults.get("sensor_campainha", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "sensor"])),
            vol.Required("entidade_sirene_alarme", default=_ensure_list(defaults.get("entidade_sirene_alarme", defaults.get("sirene", [])))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["switch", "siren", "light"])),
            vol.Optional("entidade_chime_campainha", default=_ensure_list(defaults.get("entidade_chime_campainha", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain=["switch", "siren", "light"])),
            vol.Required("moradores", default=_ensure_list(defaults.get("moradores", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="person")),
            vol.Optional("rastreadores_omada", default=_ensure_list(defaults.get("rastreadores_omada", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="device_tracker")),
            vol.Optional("notify_servicos_campainha", default=_ensure_list(defaults.get("notify_servicos_campainha", defaults.get("notify_service_name", [])))): notify_selector,
            vol.Optional("notify_servicos_sirene", default=_ensure_list(defaults.get("notify_servicos_sirene", defaults.get("notify_service_name", [])))): notify_selector,
            vol.Optional("alexa_notify_servicos_campainha", default=_ensure_list(defaults.get("alexa_notify_servicos_campainha", defaults.get("alexa_notify_service", [])))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="notify", integration="alexa_devices")),
            vol.Optional("alexa_notify_servicos_alarme", default=_ensure_list(defaults.get("alexa_notify_servicos_alarme", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="notify", integration="alexa_devices")),
            vol.Optional("alexa_msg_campainha", default=defaults.get("alexa_msg_campainha", "Atenção, campainha acionada.")): str,
            vol.Optional("alexa_msg_alarme", default=defaults.get("alexa_msg_alarme", "Atenção, o alarme foi disparado! {msg}")): str,
            vol.Optional("alexa_campainha_som_id", default=defaults.get("alexa_campainha_som_id", "amzn_sfx_doorbell_01")): str,
            vol.Optional("alexa_campainha_som_dispositivos", default=_ensure_list(defaults.get("alexa_campainha_som_dispositivos", []))): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True, domain="notify", integration="alexa_devices")),
            vol.Optional("ativar_auto_armar", default=defaults.get("ativar_auto_armar", True)): selector.BooleanSelector()
        })

class MayaKnoxConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    @staticmethod
    @callback
    def async_get_options_flow(config_entry): return MayaKnoxOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if self._async_current_entries(): return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            # Garantir que campos múltiplos sejam listas antes de salvar
            list_keys = ["sensores_perimetro", "sensores_internos", "sensor_campainha", "entidade_sirene_alarme", "entidade_chime_campainha", "moradores", "notify_servicos_campainha", "notify_servicos_sirene", "alexa_notify_servicos_campainha", "alexa_notify_servicos_alarme", "rastreadores_omada", "alexa_campainha_som_dispositivos"]
            for key in list_keys:
                if key in user_input:
                    user_input[key] = cv.ensure_list(user_input[key])
            return self.async_create_entry(title="Central Maya Knox", data=user_input)
        return self.async_show_form(step_id="user", data_schema=self._get_schema({}))

    def _get_schema(self, defaults):
        handler = MayaKnoxOptionsFlowHandler(None)
        handler.hass = self.hass
        return handler._get_schema(defaults)
