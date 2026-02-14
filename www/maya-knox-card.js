class MayaKnoxCard extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      const card = document.createElement('ha-card');
      card.header = 'Portal Maya Knox';
      this.content = document.createElement('div');
      this.content.style.padding = '0 16px 16px';
      this.content.style.textAlign = 'center';
      this.content.style.cursor = 'pointer';
      card.appendChild(this.content);
      this.appendChild(card);

      this.addEventListener('click', () => {
        this._onClick();
      });
    }

    const entityId = this.config.entity;
    const state = hass.states[entityId];
    const stateStr = state ? state.state : 'unavailable';

    // Mapeamento de traduções
    const translations = {
      'disarmed': 'DESARMADO',
      'armed_home': 'ARMADO (CASA)',
      'armed_away': 'ARMADO (AUSENTE)',
      'triggered': 'DISPARADO',
      'unavailable': 'INDISPONÍVEL',
      'unknown': 'DESCONHECIDO'
    };

    const friendlyState = translations[stateStr] || stateStr.toUpperCase();

    // Cores baseadas no estado
    let color = 'var(--primary-text-color)';
    let pulse = '';

    if (stateStr.includes('armed')) {
      color = '#f44336'; // Red
    } else if (stateStr === 'disarmed') {
      color = '#4caf50'; // Green
    } else if (stateStr === 'triggered') {
      color = '#ff9800'; // Orange
      pulse = 'animation: pulse 2s infinite;';
    }

    this.content.innerHTML = `
      <style>
        .robot-icon {
          width: 100%;
          max-width: 200px;
          height: auto;
          border-radius: 12px;
          transition: transform 0.2s;
          ${pulse}
        }
        .robot-icon:active {
          transform: scale(0.95);
        }
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0.7); }
          70% { box-shadow: 0 0 0 20px rgba(255, 152, 0, 0); }
          100% { box-shadow: 0 0 0 0 rgba(255, 152, 0, 0); }
        }
        .state-text {
          font-size: 1.5em;
          font-weight: bold;
          margin-top: 10px;
          color: ${color};
        }
      </style>
      <img class="robot-icon" src="/maya_knox_assets/logo.png" />
      <div class="state-text">${friendlyState}</div>
    `;

    this._hass = hass;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('You need to define an entity');
    }
    this.config = config;
  }

  getCardSize() {
    return 3;
  }

  _onClick() {
    const entityId = this.config.entity;
    const event = new Event('hass-more-info', {
      bubbles: true,
      cancelable: false,
      composed: true,
    });
    event.detail = { entityId };
    this.dispatchEvent(event);
  }
}

customElements.define('maya-knox-card', MayaKnoxCard);
