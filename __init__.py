import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_HOME, STATE_ON, Platform
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import add_extra_js_url

DOMAIN = "maya_knox"
PLATFORMS = [Platform.ALARM_CONTROL_PANEL]
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura o Maya Knox e inicia o monitoramento de presença."""
    config_data = entry.options or entry.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = config_data

    # --- ROTINA PROFISSIONAL: REGISTRAR ASSETS INTERNOS ---
    component_path = hass.config.path("custom_components", DOMAIN)
    assets_path = os.path.join(component_path, "assets")

    if not os.path.exists(assets_path):
        os.makedirs(assets_path)

    await hass.http.async_register_static_paths([
        StaticPathConfig(f"/{DOMAIN}_assets", assets_path, cache_headers=True),
        StaticPathConfig(f"/{DOMAIN}_www", os.path.join(component_path, "www"), cache_headers=True)
    ])

    frontend_url = f"/{DOMAIN}_www/maya-knox-card.js"
    add_extra_js_url(hass, frontend_url)

    _LOGGER.info("Identidade visual Maya Knox carregada de: %s", assets_path)
    # -------------------------------------------------------

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # VIGIA DE INTRUSÃO
    async def _verificar_intrusao(event: Event):
        estado_alarme = hass.states.get("alarm_control_panel.maya_knox_portal")
        if not estado_alarme or estado_alarme.state == "disarmed": return

        novo_estado = event.data.get("new_state")
        if novo_estado and novo_estado.state == STATE_ON:
            sensor_id = event.data.get("entity_id")
            if sensor_id in config_data.get("sensores_perimetro", []) or estado_alarme.state == "armed_away":
                await hass.services.async_call("alarm_control_panel", "alarm_trigger", {"entity_id": "alarm_control_panel.maya_knox_portal"})

    sensores = config_data.get("sensores_perimetro", []) + config_data.get("sensores_internos", [])
    entry.async_on_unload(async_track_state_change_event(hass, sensores, _verificar_intrusao))
    
    # -------------------------------------------------------
    # VIGIA DE PRESENÇA (AUTO ARMAR/DESARMAR)
    # -------------------------------------------------------
    if config_data.get("ativar_auto_armar", True):
        async def _verificar_presenca(event: Event):
            entity_id = "alarm_control_panel.maya_knox_portal"
            
            novo_estado = event.data.get("new_state")
            if not novo_estado:
                return

            # Se alguém chegou em casa (e o alarme não está desarmado) -> Desarmar
            if novo_estado.state == STATE_HOME:
                estado_atual = hass.states.get(entity_id)
                if estado_atual and estado_atual.state != "disarmed":
                    _LOGGER.info("Maya Knox: Morador chegou. Desarmando sistema.")
                    await hass.services.async_call("alarm_control_panel", "alarm_disarm", {"entity_id": entity_id})

            # Se alguém saiu, verificar se TODOS estão fora
            else:
                moradores = config_data.get("moradores", [])
                todos_fora = True
                for morador in moradores:
                    state = hass.states.get(morador)
                    # Se estado for 'home', então nem todos estão fora
                    if state and state.state == STATE_HOME:
                        todos_fora = False
                        break
                
                if todos_fora:
                    estado_atual = hass.states.get(entity_id)
                    # Só arma se não estiver já armado (home ou away)
                    if estado_atual and estado_atual.state == "disarmed":
                        _LOGGER.info("Maya Knox: Casa vazia. Armando sistema (Ausente).")
                        await hass.services.async_call("alarm_control_panel", "alarm_arm_away", {"entity_id": entity_id})

        moradores = config_data.get("moradores", [])
        if moradores:
            _LOGGER.info("Maya Knox: Monitorando presença de %s", moradores)
            entry.async_on_unload(async_track_state_change_event(hass, moradores, _verificar_presenca))
    
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Recarrega a integração."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarrega a integração."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
