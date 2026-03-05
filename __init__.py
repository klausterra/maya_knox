# -*- coding: utf-8 -*-
import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_HOME, STATE_ON, Platform
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.alarm_control_panel import AlarmControlPanelState
from homeassistant.helpers import entity_registry as er
from homeassistant.exceptions import HomeAssistantError

DOMAIN = 'maya_knox'
PLATFORMS = [Platform.ALARM_CONTROL_PANEL, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    '''Set up the Maya Knox component.'''
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    '''Set up Maya Knox from a config entry.'''
    config_data = {**entry.data, **entry.options}
    hass.data.setdefault(DOMAIN, {})

    # --- REGISTRO FRONTEND (No topo para garantir carregamento) ---
    try:
        component_path = os.path.dirname(__file__)
        www_path = os.path.join(component_path, 'www')
        brand_path = os.path.join(component_path, 'brand')
        _LOGGER.info(f'Maya Knox: Registrando caminhos estáticos em {www_path}')

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(url_path='/maya_knox_www', path=www_path, cache_headers=False),
                StaticPathConfig(url_path='/maya_knox_static', path=brand_path, cache_headers=False),
            ]
        )
    except Exception as e:
        _LOGGER.error(f'Maya Knox: Erro ao registrar recursos frontend: {e}')

    # Vigia de Intrusão (Gatilho e Relatório de Zona)
    async def _verificar_intrusao(event: Event):
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(Platform.ALARM_CONTROL_PANEL, DOMAIN, f'{DOMAIN}_main_panel')
        if not entity_id: return

        est_alarme = hass.states.get(entity_id)
        if not est_alarme or est_alarme.state not in [AlarmControlPanelState.ARMED_HOME, AlarmControlPanelState.ARMED_AWAY]:
            return

        novo_state = event.data.get('new_state')
        if novo_state and novo_state.state == STATE_ON:
            sensor_id = event.data.get('entity_id')
            if sensor_id in config_data.get('sensores_perimetro', []) or est_alarme.state == AlarmControlPanelState.ARMED_AWAY:
                hass.data[DOMAIN]['ultimo_disparo'] = sensor_id
                await hass.services.async_call('alarm_control_panel', 'alarm_trigger', {'entity_id': entity_id})

    sensores = config_data.get('sensores_perimetro', []) + config_data.get('sensores_internos', [])
    if sensores:
        entry.async_on_unload(async_track_state_change_event(hass, sensores, _verificar_intrusao))

    sensores_campainha = config_data.get('sensor_campainha', [])
    
    async def _enviar_alexa(servicos, msg):
        if not servicos:
            return
        
        for servico in servicos:
            try:
                # O serviço pode ser um nome de serviço ou uma entidade notify.*
                if '.' in servico:
                    domain, service_name = servico.split('.', 1)
                else:
                    domain, service_name = "notify", servico
                
                _LOGGER.debug(f"Maya Knox: Tentando enviar para Alexa ({servico}): {msg}")
                
                # Se o domínio for notify e o nome do serviço não existir como serviço, 
                # mas existir como entidade, usamos notify.send_message (alexa_devices oficial)
                if domain == "notify" and not hass.services.has_service(domain, service_name):
                    _LOGGER.debug(f"Maya Knox: Usando notify.send_message para entidade: {servico}")
                    await hass.services.async_call(
                        "notify",
                        "send_message",
                        {
                            "entity_id": servico,
                            "message": msg
                        },
                        blocking=True
                    )
                else:
                    # Tenta serviço específico (alexa_media ou outro)
                    await hass.services.async_call(
                        domain, 
                        service_name, 
                        {"message": msg, "data": {"type": "announce"}},
                        blocking=True
                    )
                    _LOGGER.info(f"Maya Knox: Notificação enviada para {servico}")
            except Exception as e:
                _LOGGER.error(f"Maya Knox: Erro ao enviar para Alexa {servico}: {e}")

    async def _tocar_campainha(event=None):
        novo_state = event.data.get('new_state') if event else None
        if (novo_state and novo_state.state == STATE_ON) or event is None:
            _LOGGER.info('Maya Knox: Campainha acionada!')
            notify_services = config_data.get('notify_servicos_campainha', config_data.get('notify_service_name', []))
            if isinstance(notify_services, str): notify_services = [notify_services]
            if not notify_services: notify_services = ['notify.notify']

            alexa_services = config_data.get('alexa_notify_servicos_campainha', config_data.get('alexa_notify_service', []))
            if isinstance(alexa_services, str): alexa_services = [alexa_services] if alexa_services else []

            nome_zona = 'Campainha de Teste'
            if event:
                sensor_id = event.data.get('entity_id')
                s_state = hass.states.get(sensor_id)
                nome_zona = s_state.attributes.get('friendly_name', sensor_id) if s_state else sensor_id

            dados = {
                'title': ' CAMPAINHA!',
                'message': f'Movimento ou toque detectado em: {nome_zona}',
                'data': {
                    'push': {
                        'sound': {
                            'name': 'default',
                            'critical': 1,
                            'volume': 1.0
                        },
                        'category': 'DOORBELL'
                    },
                    'channel': 'Doorbell',
                    'ttl': 0,
                    'priority': 'high'
                }
            }
            
            for ns in notify_services:
                domain, service = ns.split('.', 1) if '.' in ns else ('notify', ns)
                await hass.services.async_call(domain, service, dados)

            if alexa_services:
                alexa_msg_template = config_data.get('alexa_msg_campainha', 'Atenção, campainha acionada.')
                mensagem_alexa = alexa_msg_template.replace('{zona}', nome_zona)
                await _enviar_alexa(alexa_services, mensagem_alexa)

            # Novo: Som de campainha na Alexa
            alexa_sound_id = config_data.get('alexa_campainha_som_id')
            alexa_sound_devices = config_data.get('alexa_campainha_som_dispositivos', [])
            if alexa_sound_id and alexa_sound_devices:
                registry = er.async_get(hass)
                for device_entity in alexa_sound_devices:
                    if device_entity.startswith('notify.'):
                        # Se for entidade notify, tentamos extrair o device_id ou usar o serviço speak se suportado?
                        # Se for uma entidade de notify direta (como alexa_devices)
                        # Vamos tentar pegar o device_id pelo entity_registry.
                        entry_reg = registry.async_get(device_entity)
                        if entry_reg and entry_reg.device_id:
                            await hass.services.async_call(
                                'alexa_devices', 
                                'send_sound', 
                                {
                                    'sound': alexa_sound_id,
                                    'device_id': entry_reg.device_id
                                }
                            )
                    else:
                        # Legado (config antiga que tinha media_player)
                        entry_reg = registry.async_get(device_entity)
                        if entry_reg and entry_reg.device_id:
                            await hass.services.async_call(
                                'alexa_devices', 
                                'send_sound', 
                                {
                                    'sound': alexa_sound_id,
                                    'device_id': entry_reg.device_id
                                }
                            )

            # Novo: Acionar Campainha Física (Chime)
            chime_entities = config_data.get('entidade_chime_campainha', [])
            if chime_entities:
                await hass.services.async_call('homeassistant', 'turn_on', {'entity_id': chime_entities})

    if sensores_campainha:
        entry.async_on_unload(async_track_state_change_event(hass, sensores_campainha, _tocar_campainha))

    # Auto-Armar/Desarmar por GPS (Moradores)
    if config_data.get('ativar_auto_armar'):
        moradores = config_data.get('moradores', []) + config_data.get('rastreadores_omada', [])

        async def _verificar_presenca(event: Event):
            registry = er.async_get(hass)
            entity_id = registry.async_get_entity_id(Platform.ALARM_CONTROL_PANEL, DOMAIN, f'{DOMAIN}_main_panel')
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
                _LOGGER.info('Maya Knox: Todos os moradores saíram. Armando automático.')
                await hass.services.async_call('alarm_control_panel', 'alarm_arm_away', {'entity_id': entity_id})
            elif not todos_fora and est_alarme.state == AlarmControlPanelState.ARMED_AWAY:
                _LOGGER.info('Maya Knox: Morador chegou. Desarmando automático.')
                await hass.services.async_call('alarm_control_panel', 'alarm_disarm', {'entity_id': entity_id})

        if moradores:
            entry.async_on_unload(async_track_state_change_event(hass, moradores, _verificar_presenca))

    # --- Serviços de Teste (Sempre disponíveis) ---
    async def test_campainha(call):
        _LOGGER.info("Maya Knox: Testando campainha...")
        await _tocar_campainha(None)
        
    async def test_alarme(call):
        _LOGGER.info("Maya Knox: Testando alarme...")
        hass.data[DOMAIN]["ultimo_disparo"] = "Teste de Sistema"
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(Platform.ALARM_CONTROL_PANEL, DOMAIN, f'{DOMAIN}_main_panel')
        if entity_id:
            await hass.services.async_call('alarm_control_panel', 'alarm_trigger', {'entity_id': entity_id})
        else:
            _LOGGER.error("Maya Knox: Entidade de alarme não encontrada para o teste.")

    hass.services.async_register(DOMAIN, "test_campainha", test_campainha)
    hass.services.async_register(DOMAIN, "test_alarme", test_alarme)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
