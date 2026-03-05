from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

DOMAIN = "maya_knox"

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Maya Knox buttons."""
    async_add_entities([
        MayaKnoxTestCampainhaButton(config_entry),
        MayaKnoxTestAlarmeButton(config_entry),
    ])

class MayaKnoxTestCampainhaButton(ButtonEntity):
    """Button to test the doorbell."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._config_entry = config_entry
        self._attr_name = "Testar Campainha"
        self._attr_unique_id = f"{config_entry.entry_id}_test_campainha"
        self._attr_icon = "mdi:doorbell-video"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Maya Knox Security",
            "manufacturer": "HiperMaya",
            "model": "Portal",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.hass.services.async_call(DOMAIN, "test_campainha", {})

class MayaKnoxTestAlarmeButton(ButtonEntity):
    """Button to test the alarm."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the button."""
        self._config_entry = config_entry
        self._attr_name = "Testar Alarme"
        self._attr_unique_id = f"{config_entry.entry_id}_test_alarme"
        self._attr_icon = "mdi:alarm-bell"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": "Maya Knox Security",
            "manufacturer": "HiperMaya",
            "model": "Portal",
        }

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.hass.services.async_call(DOMAIN, "test_alarme", {})
