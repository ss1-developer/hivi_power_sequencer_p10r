"""The HiVi Power Sequencer P10R integration."""

from __future__ import annotations

import logging

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
from .tcp_client import TCPClient

_LOGGER = logging.getLogger(__name__)


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

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(entry.entry_id, {})
        hass.data[DOMAIN][entry.entry_id] = {
            "tcp_client": None,
        }

        tcp_client = TCPClient.get_instance(host=host, port=port)
        hass.data[DOMAIN][entry.entry_id]["tcp_client"] = tcp_client

        await hass.config_entries.async_forward_entry_setups(entry, ["button"])

        return True

    except Exception as err:  # pylint: disable=broad-except
        raise ConfigEntryError(f"Unexpected error: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目"""
    _LOGGER.debug(f"Unloading {DOMAIN} entry: {entry.entry_id}")

    try:
        # 安全获取配置数据
        domain_data = hass.data.get(DOMAIN, {})
        entry_data = domain_data.get(entry.entry_id)

        if not entry_data:
            _LOGGER.warning(f"No entry data found for {entry.entry_id}")
            return True

        # 清理 TCP 客户端
        tcp_client = entry_data.get("tcp_client")
        if tcp_client:
            _LOGGER.debug("Cleaning up TCP client")
            if hasattr(tcp_client, "clean") and callable(tcp_client.clean):
                await tcp_client.clean()  # type: ignore # 异步清理

        # 卸载平台
        unload_ok = await hass.config_entries.async_unload_platforms(entry, ["button"])

        if unload_ok:
            # 清理 hass.data
            if entry.entry_id in hass.data[DOMAIN]:
                del hass.data[DOMAIN][entry.entry_id]
                _LOGGER.debug(f"Removed entry {entry.entry_id} from hass.data")

            # 如果域数据为空，清理整个域
            if not hass.data.get(DOMAIN):
                del hass.data[DOMAIN]
                _LOGGER.debug(f"Removed domain {DOMAIN} from hass.data")

        return unload_ok

    except Exception as e:
        _LOGGER.error(f"Error unloading {DOMAIN} entry {entry.entry_id}: {e}")
        return False
