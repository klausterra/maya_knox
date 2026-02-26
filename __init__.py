import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_HOME, STATE_ON, Platform
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.alarm_control_panel import AlarmControlPanelState

DOMAIN = "maya_knox"
PLATFORMS = [Platform.ALARM_CONTROL_PANEL]

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers import entity_registry as er

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Maya Knox from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    config_data = entry.data

    # --- REGISTRO FRONTEND (No topo para garantir carregamento) ---
    try:
        component_path = os.path.dirname(__file__)
        www_path = os.path.join(component_path, "www")
        brand_path = os.path.join(component_path, "brand")
        _LOGGER.info(f"Maya Knox: Registrando caminhos estáticos em {www_path}")
        
        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(url_path="/maya_knox_www", path=www_path, cache_headers=False),
                StaticPathConfig(url_path="/maya_knox_assets", path=brand_path, cache_headers=True),
            ]
        )
    except Exception as e:
        _LOGGER.error(f"Maya Knox: Erro ao registrar recursos frontend: {e}")

    # Vigia de Intrusão (Gatilho e Relatório de Zona)
    async def _verificar_intrusao(event: Event):
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(Platform.ALARM_CONTROL_PANEL, DOMAIN, f"{DOMAIN}_main_panel")
        if not entity_id: return

        est_alarme = hass.states.get(entity_id)
        if not est_alarme or est_alarme.state not in [AlarmControlPanelState.ARMED_HOME, AlarmControlPanelState.ARMED_AWAY]: 
            return
        
        novo_state = event.data.get("new_state")
        if novo_state and novo_state.state == STATE_ON:
            sensor_id = event.data.get("entity_id")
            if sensor_id in config_data.get("sensores_perimetro", []) or est_alarme.state == AlarmControlPanelState.ARMED_AWAY:
                hass.data[DOMAIN]["ultimo_disparo"] = sensor_id
                await hass.services.async_call("alarm_control_panel", "alarm_trigger", {"entity_id": entity_id})

    sensores = config_data.get("sensores_perimetro", []) + config_data.get("sensores_internos", [])
    if sensores:
        entry.async_on_unload(async_track_state_change_event(hass, sensores, _verificar_intrusao))

    # Vigia de Campainha
    sensores_campainha = config_data.get("sensor_campainha", [])
    if sensores_campainha:
        async def _tocar_campainha(event: Event):
            novo_state = event.data.get("new_state")
            if novo_state and novo_state.state == STATE_ON:
                _LOGGER.info("Maya Knox: Campainha acionada!")
                notify_service = config_data.get("notify_service_name", "notify.notify")
                alexa_service = config_data.get("alexa_notify_service", "")
                domain, service = notify_service.split(".", 1) if "." in notify_service else ("notify", "notify")
                
                sensor_id = event.data.get("entity_id")
                s_state = hass.states.get(sensor_id)
                nome_zona = s_state.attributes.get("friendly_name", sensor_id) if s_state else sensor_id
                
                dados = {
                    "title": "🔔 CAMPAINHA!",
                    "message": f"Movimento ou toque detectado em: {nome_zona}"
                }
                await hass.services.async_call(domain, service, dados)
                
                if alexa_service:
                    alexa_msg_template = config_data.get("alexa_msg_campainha", "Atenção, campainha acionada.")
                    mensagem_alexa = alexa_msg_template.replace("{zona}", nome_zona)
                    
                    a_domain, a_service = alexa_service.split(".", 1) if "." in alexa_service else ("notify", alexa_service.replace("notify.", ""))
                    alexa_dados = {
                        "message": mensagem_alexa,
                        "data": {"type": "tts"}
                    }
                    await hass.services.async_call(a_domain, a_service, alexa_dados)

        entry.async_on_unload(async_track_state_change_event(hass, sensores_campainha, _tocar_campainha))

    # Auto-Armar/Desarmar por GPS (Moradores)
    if config_data.get("ativar_auto_armar"):
        moradores = config_data.get("moradores", [])
        
        async def _verificar_presenca(event: Event):
            registry = er.async_get(hass)
            entity_id = registry.async_get_entity_id(Platform.ALARM_CONTROL_PANEL, DOMAIN, f"{DOMAIN}_main_panel")
            if not entity_id: return
            est_alarme = hass.states.get(entity_id)
            if not est_alarme: return

            todos_fora = True
            for m in moradores:
                s = hass.states.get(m)
                if s and s.state == STATE_HOME:
                    todos_fora = False
                    break
            
            if todos_fora and est_alarme.state == AlarmControlPanelState.DISARMED:
                _LOGGER.info("Maya Knox: Todos os moradores saíram. Armando automático.")
                await hass.services.async_call("alarm_control_panel", "alarm_arm_away", {"entity_id": entity_id})
            elif not todos_fora and est_alarme.state == AlarmControlPanelState.ARMED_AWAY:
                _LOGGER.info("Maya Knox: Morador chegou. Desarmando automático.")
                await hass.services.async_call("alarm_control_panel", "alarm_disarm", {"entity_id": entity_id})

        if moradores:
            entry.async_on_unload(async_track_state_change_event(hass, moradores, _verificar_presenca))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)