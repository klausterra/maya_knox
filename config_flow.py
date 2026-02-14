import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

DOMAIN = "maya_knox"

class MayaKnoxOptionsFlowHandler(config_entries.OptionsFlow):
    """Painel Contínuo de Edição de Zonas (Botão Configurar)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Busca os dados atuais de forma segura
        opcoes = self.config_entry.options or self.config_entry.data

        data_schema = vol.Schema({
            vol.Required("sensores_perimetro", default=opcoes.get("sensores_perimetro", [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "camera"])
            ),
            vol.Required("sensores_internos", default=opcoes.get("sensores_internos", [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="binary_sensor")
            ),
            vol.Required("moradores", default=opcoes.get("moradores", [])): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="person")
            ),
            vol.Optional("ativar_auto_armar", default=opcoes.get("ativar_auto_armar", True)): selector.BooleanSelector()
        })

        return self.async_show_form(step_id="init", data_schema=data_schema)


class MayaKnoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Interface de Instalação Inicial do Maya Knox."""
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MayaKnoxOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        # TRAVA DE SEGURANÇA: Impede que o cliente tente instalar de novo se já existir
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Central Maya Knox", data=user_input)

        data_schema = vol.Schema({
            vol.Required("sensores_perimetro"): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain=["binary_sensor", "camera"])
            ),
            vol.Required("sensores_internos"): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="binary_sensor")
            ),
            vol.Required("moradores"): selector.EntitySelector(
                selector.EntitySelectorConfig(multiple=True, domain="person")
            ),
            vol.Optional("ativar_auto_armar", default=True): selector.BooleanSelector()
        })
        
        return self.async_show_form(step_id="user", data_schema=data_schema)