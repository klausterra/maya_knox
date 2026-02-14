from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)

DOMAIN = "maya_knox"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Configura a entidade do alarme puxando os dados do instalador."""
    config_data = config_entry.options if config_entry.options else config_entry.data
    async_add_entities([MayaKnoxAlarm("Maya Knox Portal", config_data)])

class MayaKnoxAlarm(AlarmControlPanelEntity):
    """Representação do Alarme Maya Knox."""

    def __init__(self, name, config_data):
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_main_panel"
        self._attr_alarm_state = AlarmControlPanelState.DISARMED 
        self._config_data = config_data
        
        # Logo personalizado da integração (via assets profissionais)
        self._attr_entity_picture = f"/{DOMAIN}_assets/logo.png"
        self._attr_icon = "mdi:shield-lock"

        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_HOME 
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.TRIGGER
        )
        self._attr_code_arm_required = False
        self._attr_code_format = None



    async def _enviar_notificacao(self, titulo, mensagem, disparo=False):
        """Envia mensagem push nativa para o app do Home Assistant com Snapshot."""
        dados = {
            "title": titulo,
            "message": mensagem,
            "data": {}
        }
        
        if disparo:
            sensores_perimetro = self._config_data.get("sensores_perimetro", [])
            camera_alvo = None
            
            for sensor in sensores_perimetro:
                if sensor.startswith("camera."):
                    camera_alvo = sensor
                    break
            
            if camera_alvo:
                dados["data"]["image"] = f"/api/camera_proxy/{camera_alvo}"
                dados["data"]["entity_id"] = camera_alvo 
                
            dados["data"]["actions"] = [
                {
                    "action": "URI", 
                    "title": "📹 Abrir Central Maya", 
                    "uri": "/lovelace/default_view" 
                }
            ]
            
        await self.hass.services.async_call("notify", "notify", dados, blocking=False)

    async def async_alarm_disarm(self, code=None):
        self._attr_alarm_state = AlarmControlPanelState.DISARMED
        self.async_write_ha_state()
        await self._enviar_notificacao("🟢 Maya Knox", "Sistema Desarmado com sucesso.")

    async def async_alarm_arm_home(self, code=None):
        self._attr_alarm_state = AlarmControlPanelState.ARMED_HOME
        self.async_write_ha_state()
        await self._enviar_notificacao("🟠 Maya Knox", "Armado (Casa). Proteção de perímetro ativada.")

    async def async_alarm_arm_away(self, code=None):
        self._attr_alarm_state = AlarmControlPanelState.ARMED_AWAY
        self.async_write_ha_state()
        await self._enviar_notificacao("🔴 Maya Knox", "Armado (Ausente). Proteção total ativada.")

    async def async_alarm_trigger(self, code=None):
        if self._attr_alarm_state != AlarmControlPanelState.TRIGGERED:
            self._attr_alarm_state = AlarmControlPanelState.TRIGGERED
            self.async_write_ha_state()
            await self._enviar_notificacao(
                "🚨 ALARME DISPARADO 🚨", 
                "Violação detectada pelos sensores!", 
                disparo=True
            )