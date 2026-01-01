"""The HiVi Power Sequencer P10R integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryError,
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
)
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HiVi Power Sequencer P10R from a config entry."""

    try:
        # TODO 1. Create API instance
        # TODO 2. Validate the API connection (and authentication)
        # TODO 3. Store an API object for your platforms to access
        entry.runtime_data = None

        # await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

        host = entry.data["host"]
        port = entry.data["port"]

        identifiers = {(DOMAIN, f"hivi_power_sequencer_p10r_{host}_{port}")}
        manufacturer = "HiVi"
        model = "P10R"
        sw_version = None

        # 获取设备注册表
        device_registry = async_get_device_registry(hass)

        # 注册广播主机设备
        device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers=identifiers,  # 唯一标识符
            manufacturer=manufacturer,
            model=model,
            sw_version=sw_version,
            name=f"HiViPowerSequencerP10R ({host}:{port})",
        )

        await hass.config_entries.async_forward_entry_setups(entry, ["button"])

        return True
    except Exception as err:  # pylint: disable=broad-except
        raise ConfigEntryError(f"Unexpected error: {err}")


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
    return await hass.config_entries.async_unload_platforms(entry, ["button"])
