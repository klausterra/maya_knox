import logging
import os  # <--- IMPORTANTE PARA LER PASTAS
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
    # 1. Descobre onde a pasta do componente está no disco
    component_path = hass.config.path("custom_components", DOMAIN)
    # 2. Aponta para a subpasta 'assets' que criamos
    assets_path = os.path.join(component_path, "assets")
    
    # Cria a pasta caso não exista
    if not os.path.exists(assets_path):
        os.makedirs(assets_path)

    # 3. Cria uma URL virtual (/maya_knox_assets) que aponta para essa pasta física
    # O cache_headers=True garante que a imagem carregue instantaneamente
    await hass.http.async_register_static_paths([
        StaticPathConfig(f"/{DOMAIN}_assets", assets_path, cache_headers=True),
        StaticPathConfig(f"/{DOMAIN}_www", os.path.join(component_path, "www"), cache_headers=True)
    ])
    
    # 4. Registra o recurso do Lovelace automaticamente
    # Isso faz com que o dashboard carregue o JS sem o usuário precisar configurar manualmente
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
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry): 
    """Recarrega a integração."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry): 
    """Descarrega a integração."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)