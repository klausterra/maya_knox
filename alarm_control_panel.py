from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity, AlarmControlPanelEntityFeature, AlarmControlPanelState
import os
import json
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "maya_knox"

async def async_setup_entry(hass, config_entry, async_add_entities):
    config_data = {**config_entry.data, **config_entry.options}
    async_add_entities([MayaKnoxAlarm("Maya Knox Portal", config_data)])

from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

class MayaKnoxAlarm(AlarmControlPanelEntity):
    def __init__(self, name, config_data):
        super().__init__()
        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_main_panel"
        self._attr_state = AlarmControlPanelState.DISARMED 
        self._config_data = config_data
        self._attr_entity_picture = "/maya_knox_assets/icon.png?v=2"
        self._attr_code_format = None
        self._attr_code_arm_required = False
        self._attr_supported_features = AlarmControlPanelEntityFeature.ARM_HOME | AlarmControlPanelEntityFeature.ARM_AWAY | AlarmControlPanelEntityFeature.TRIGGER
        self._sensor_disparo = None
        self._logs = []
        self._log_file = None
        # O _log_file serÃ¡ definido no async_added_to_hass quando tivermos acesso ao caminho da config
        
    async def async_added_to_hass(self):
        """Carregar logs quando a entidade Ã© adicionada."""
        await super().async_added_to_hass()
        self._log_file = self.hass.config.path("maya_knox_logs.json")
        self._logs = await self.hass.async_add_executor_job(self._load_logs)

    def _load_logs(self):
        """Carregar logs do disco."""
        if not self._log_file:
            return []
        try:
            if os.path.exists(self._log_file):
                with open(self._log_file, "r") as f:
                    logs = json.load(f)
                    _LOGGER.info("Maya Knox: Logs persistentes carregados.")
                    return logs
        except Exception as e:
            _LOGGER.error(f"Erro ao carregar logs: {e}")
        return []

    def _save_logs(self, logs_to_save):
        """Salvar logs no disco."""
        if not self._log_file:
            return
        try:
            with open(self._log_file, "w") as f:
                json.dump(logs_to_save, f)
        except Exception as e:
            _LOGGER.error(f"Erro ao salvar logs: {e}")

    @property
    def alarm_state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        sensores = self._config_data.get("sensores_perimetro", []) + self._config_data.get("sensores_internos", [])
        return {
            "sensor_disparo": self._sensor_disparo,
            "sensors": sensores,
            "recent_logs": self._logs[-10:] # Keep last 10
        }

    def _add_log(self, action, info=""):
        now = dt_util.now().strftime("%d/%m %H:%M:%S")
        self._logs.append({"time": now, "action": action, "info": info})
        if len(self._logs) > 50: self._logs.pop(0)
        
        logs_copy = list(self._logs)
        
        if hasattr(self, 'hass') and self.hass:
            self.hass.async_add_executor_job(self._save_logs, logs_copy)
            self.async_write_ha_state()
        else:
            self._save_logs(logs_copy)

    async def async_alarm_trigger(self, code=None):
        self._attr_state = AlarmControlPanelState.TRIGGERED
        s_id = self.hass.data.get(DOMAIN, {}).get("ultimo_disparo", "Desconhecido")
        s_state = self.hass.states.get(s_id)
        nome_zona = s_state.attributes.get("friendly_name", s_id) if s_state else s_id
        self._sensor_disparo = nome_zona
        
        self._add_log("DISPARO", nome_zona)
        await self._controlar_sirene(True)
        self.async_write_ha_state()
        await self._enviar_notificacao("🚨 INVASÃO!", f"Disparo em: {nome_zona}", disparo=True)

    async def _controlar_sirene(self, ligar=True):
        ent = self._config_data.get("entidade_sirene_alarme")
        if ent: await self.hass.services.async_call("homeassistant", "turn_on" if ligar else "turn_off", {"entity_id": ent})

    async def async_alarm_disarm(self, code=None):
        self._attr_state = AlarmControlPanelState.DISARMED
        self._sensor_disparo = None
        self._add_log("Desarmado", "Usuário")
        await self._controlar_sirene(False)
        self.async_write_ha_state()
        await self._enviar_notificacao("🛡️ Sistema Desarmado", "O alarme foi desativado.")

    async def async_alarm_arm_home(self, code=None): 
        self._attr_state = AlarmControlPanelState.ARMED_HOME
        self._add_log("Armado (Casa)")
        self.async_write_ha_state()
        await self._enviar_notificacao("🏠 Armado (Casa)", "O alarme perimetral foi ativado.")

    async def async_alarm_arm_away(self, code=None): 
        self._attr_state = AlarmControlPanelState.ARMED_AWAY
        self._add_log("Armado (Rua)")
        self.async_write_ha_state()
        await self._enviar_notificacao("🔒 Armado (Rua)", "Todos os sensores foram ativados.")

    async def _enviar_notificacao(self, titulo, msg, disparo=False):
        dados = {"title": titulo, "message": msg, "data": {}}
        if disparo:
            dados["data"].update({
                "push": { "category": "ALARM",
                    "sound": {
                        "name": "default",
                        "critical": 1,
                        "volume": 1.0
                    }
                },
                "channel": "Alarm", "ttl": 0,
                "priority": "high",
                "color": "red"
            })
            cam = next((s for s in self._config_data.get("sensores_perimetro", []) if s.startswith("camera.")), None)
            if cam: 
                dados["data"]["image"] = f"/api/camera_proxy/{cam}"
                dados["data"]["entity_id"] = cam
        
        notify_services = self._config_data.get("notify_servicos_sirene", self._config_data.get("notify_service_name", []))
        if isinstance(notify_services, str): notify_services = [notify_services]
        if not notify_services: notify_services = ["notify.notify"]
        
        
        for ns in notify_services:
            domain, service = ns.split(".", 1) if "." in ns else ("notify", ns)
            await self.hass.services.async_call(domain, service, dados)
        
        alexa_services = self._config_data.get("alexa_notify_servicos_alarme", self._config_data.get("alexa_notify_service", []))
        if isinstance(alexa_services, str): alexa_services = [alexa_services] if alexa_services else []
        if alexa_services and disparo:
            _LOGGER.info(f"Maya Knox: Iniciando notificações Alexa para alarme: {alexa_services}")
            alexa_msg_template = self._config_data.get("alexa_msg_alarme", "Atenção, o alarme foi disparado! {msg}")
            zona_nome = self._sensor_disparo if self._sensor_disparo else "Zona Desconhecida"
            mensagem_alexa = alexa_msg_template.replace("{msg}", msg).replace("{zona}", zona_nome)
            
            alexa_dados = {
                "message": mensagem_alexa,
            }

            for alexa_service in alexa_services:
                _LOGGER.info(f"Maya Knox: Tentando notificar Alexa (Alarme): {alexa_service}")
                try:
                    # O serviço pode ser um nome de serviço ou uma entidade notify.*
                    if alexa_service.startswith('notify.'):
                        domain, service_name = alexa_service.split('.', 1)
                        
                        # Se existe o serviço específico (ex: formato legado ou alexa_media por dispositivo)
                        if self.hass.services.has_service(domain, service_name):
                            await self.hass.services.async_call(
                                domain, 
                                service_name, 
                                {"message": mensagem_alexa, "data": {"type": "announce"}},
                                blocking=True
                            )
                        else:
                            # Caso contrário, usamos o serviço unificado notify.send_message (alexa_devices oficial)
                            await self.hass.services.async_call(
                                "notify",
                                "send_message",
                                {
                                    "entity_id": alexa_service,
                                    "message": mensagem_alexa
                                },
                                blocking=True
                            )
                        _LOGGER.info(f"Maya Knox: Notificação de alarme enviada para {alexa_service}")
                    elif self.hass.services.has_service('notify', 'alexa_media'):
                        # Legado (alexa_media via serviço centralizado)
                        alexa_media_dados = {
                            'message': mensagem_alexa,
                            'data': {'type': 'announce', 'method': 'all'},
                            'target': [alexa_service]
                        }
                        await self.hass.services.async_call('notify', 'alexa_media', alexa_media_dados)
                        _LOGGER.info(f"Maya Knox: Notificação de alarme enviada via alexa_media para {alexa_service}")
                except Exception as e:
                    _LOGGER.error(f"Maya Knox: Erro ao enviar para Alexa {alexa_service}: {e}")
