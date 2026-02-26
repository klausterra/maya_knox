console.info("%c MAYA KNOX PORTAL %c 1.1.0 ", "color: white; background: #00d4ff; font-weight: 700;", "color: #00d4ff; background: #1c1c1c; font-weight: 700;");

class MayaKnoxCard extends HTMLElement {
  set hass(hass) {
    const entityId = this.config.entity;
    const state = hass.states[entityId];
    const name = this.config.name || "Maya Knox";
    const logoUrl = "/maya_knox_assets/logo.png?v=10";

    if (!this.content) {
      this.innerHTML = `
        <ha-card style="overflow: hidden; border-radius: 15px; background: #1c1c1c; color: white; padding: 16px; text-align: center; position: relative;">
            <div id="btn-settings" style="position: absolute; top: 10px; right: 10px; cursor: pointer; color: #888; transition: color 0.3s;" onmouseover="this.style.color='white'" onmouseout="this.style.color='#888'">
                <ha-icon icon="mdi:cog"></ha-icon>
            </div>
            <div id="status-glow" style="width: 100px; height: 100px; margin: 0 auto; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: all 0.5s ease; box-shadow: 0 0 15px #4caf50;">
              <img src="${logoUrl}" style="width: 90px; height: 90px; border-radius: 50%; border: 2px solid #00d4ff;">
            </div>
            <div style="margin-top: 10px;">
              <span style="font-size: 18px; font-weight: bold; display: block;">${name}</span>
              <span id="state-text" style="font-size: 12px; text-transform: uppercase;">Desarmado</span>
              <div id="sensor-text" style="font-size: 11px; color: #ff4d4d; font-weight: bold; margin-top: 5px;"></div>
            </div>

            <div style="margin-top: 20px; text-align: left; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px;">
                <div style="font-size: 12px; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 8px; color: #00d4ff;">SENSORES</div>
                <div id="sensor-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;"></div>
            </div>

            <div style="margin-top: 10px; text-align: left; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px;">
                <div style="font-size: 12px; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 8px; color: #00d4ff;">REGISTRO</div>
                <div id="log-list" style="font-size: 11px; color: #aaa; max-height: 100px; overflow-y: auto;"></div>
            </div>

            <div style="margin-top: 15px; display: flex; justify-content: space-around; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 10px;">
              <div id="btn-home" style="cursor: pointer; color: #ffa500; display: flex; flex-direction: column; align-items: center; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                  <ha-icon icon="mdi:shield-home" style="--mdc-icon-size: 32px;"></ha-icon>
                  <span style="font-size: 10px; margin-top: 4px; font-weight: bold;">CASA</span>
              </div>
              <div id="btn-away" style="cursor: pointer; color: #ff4d4d; display: flex; flex-direction: column; align-items: center; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                  <ha-icon icon="mdi:shield-lock" style="--mdc-icon-size: 32px;"></ha-icon>
                  <span style="font-size: 10px; margin-top: 4px; font-weight: bold;">RUA</span>
              </div>
              <div id="btn-disarm" style="cursor: pointer; color: #4caf50; display: flex; flex-direction: column; align-items: center; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
                  <ha-icon icon="mdi:shield-off" style="--mdc-icon-size: 32px;"></ha-icon>
                  <span style="font-size: 10px; margin-top: 4px; font-weight: bold;">DESARMAR</span>
              </div>
            </div>
        </ha-card>
      `;
      this.content = this.querySelector("ha-card");
      this.querySelector("#btn-home").onclick = () => hass.callService("alarm_control_panel", "alarm_arm_home", { entity_id: entityId });
      this.querySelector("#btn-away").onclick = () => hass.callService("alarm_control_panel", "alarm_arm_away", { entity_id: entityId });
      this.querySelector("#btn-disarm").onclick = () => hass.callService("alarm_control_panel", "alarm_disarm", { entity_id: entityId });
      this.querySelector("#btn-settings").onclick = () => {
        const event = new Event("hass-more-info", { bubbles: true, composed: true });
        event.detail = { entityId: "alarm_control_panel.maya_knox_portal" };
        this.dispatchEvent(event);
      };
    }

    const stateText = this.querySelector("#state-text");
    const glow = this.querySelector("#status-glow");
    const sensorText = this.querySelector("#sensor-text");
    const sensorList = this.querySelector("#sensor-list");
    const logList = this.querySelector("#log-list");

    if (state) {
      // Status Principal
      const traducao = {
        "disarmed": "DESARMADO",
        "armed_home": "ARMADO (CASA)",
        "armed_away": "ARMADO (RUA)",
        "triggered": "DISPARADO"
      };

      const s = state.state.toLowerCase();
      stateText.innerHTML = traducao[s] || state.state.toUpperCase();
      const lastSensor = state.attributes.sensor_disparo || "";
      if (state.state === "disarmed") { glow.style.boxShadow = "0 0 15px #4caf50"; stateText.style.color = "#4caf50"; sensorText.innerHTML = ""; }
      else if (state.state === "triggered") { glow.style.boxShadow = "0 0 25px #ff0000"; stateText.style.color = "#ff0000"; sensorText.innerHTML = `DISPARO EM: ${lastSensor}`; }
      else { glow.style.boxShadow = "0 0 15px #ffa500"; stateText.style.color = "#ffa500"; sensorText.innerHTML = ""; }

      // Lista de Sensores
      const sensors = state.attributes.sensors || [];
      sensorList.innerHTML = sensors.map(sId => {
        const sState = hass.states[sId];
        const sName = sState ? (sState.attributes.friendly_name || sId) : sId;
        const isOpen = sState && (sState.state === 'on' || sState.state === 'open');
        const color = isOpen ? '#ff4d4d' : '#4caf50';
        const icon = isOpen ? 'mdi:alert-circle' : 'mdi:check-circle';
        return `
              <div style="display: flex; align-items: center; gap: 6px;">
                  <ha-icon icon="${icon}" style="color: ${color}; --mdc-icon-size: 14px;"></ha-icon>
                  <span style="font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: ${color}; max-width: 100px;">${sName}</span>
              </div>
          `;
      }).join("");

      // Lista de Logs
      const logs = state.attributes.recent_logs || [];
      if (logs.length === 0) {
        logList.innerHTML = `<div style="text-align: center; padding: 10px 0; color: #666; font-style: italic;">Nenhum evento foi registrado ainda...</div>`;
      } else {
        logList.innerHTML = logs.slice().reverse().map(log => `
            <div style="margin-bottom: 4px; border-bottom: 1px solid #2c2c2c; padding-bottom: 2px; display: flex; justify-content: space-between;">
                <span><span style="color: #4caf50;">[${log.time}]</span> <span style="color: white;">${log.action}</span></span>
                <span style="color: #888; font-style: italic;">${log.info}</span>
            </div>
        `).join("");
      }
    }
  }
  setConfig(config) { this.config = config; }
  static getStubConfig() { return { entity: "alarm_control_panel.maya_knox_portal", name: "Central Maya Knox" } }
}
customElements.define("maya-knox-card", MayaKnoxCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "maya-knox-card",
  name: "Maya Knox Security",
  description: "Painel de controle avançado Maya Knox para Hipercube.",
  icon: "mdi:shield-check",
  preview: true,
});