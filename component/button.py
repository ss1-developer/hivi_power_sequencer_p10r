# custom_components/ss-power-sequencer-p10r/switch.py
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import voluptuous as vol
from homeassistant.helpers.entity import Entity
import logging
from homeassistant.components.button import ButtonEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """实体平台设置"""

    host = entry.data["host"]
    port = entry.data["port"]

    _LOGGER.debug(f"button async_setup_entry host = {host}")
    _LOGGER.debug(f"button async_setup_entry port = {port}")

    # 定义按钮配置
    button_configs = [
        (1, "CH1_On"),
        (2, "CH1_Off"),
        (3, "CH2_On"),
        (4, "CH2_Off"),
        (5, "CH3_On"),
        (6, "CH3_Off"),
        (7, "CH4_On"),
        (8, "CH4_Off"),
        (9, "CH5_On"),
        (10, "CH5_Off"),
        (11, "CH6_On"),
        (12, "CH6_Off"),
        (13, "CH7_On"),
        (14, "CH7_Off"),
        (15, "CH8_On"),
        (16, "CH8_Off"),
        (17, "PowerSync"),
    ]

    # 一次性创建所有按钮
    buttons = [
        PowerSequencerButton(entry, host, port, btn_name)
        for btn_idx, btn_name in button_configs
    ]

    async_add_entities(buttons)

    return True


class PowerSequencerButton(ButtonEntity):
    """代表电源时序器的虚拟实体"""

    def __init__(self, entry, host, port, btn_name):
        _LOGGER.debug(f"PowerSequencerButton __init__ host = {host} port = {port}")
        device_identifiers = {(DOMAIN, f"hivi_power_sequencer_p10r_{host}_{port}")}
        self._entry = entry
        self._attr_device_info = {"identifiers": device_identifiers}
        self._attr_unique_id = f"hivi_power_sequencer_p10r_{host}_{port}_{btn_name}"
        self._attr_name = f"{btn_name}"
        # self._attr_entity_id = f"button.hivi_power_sequencer_p10r_{host}_{port}_{btn_name.lower().replace(' ', '_')}"

    async def async_press(self) -> None:
        """按钮按下时的处理逻辑"""
        _LOGGER.info(f"{self._attr_name} press")
        # 这里实现实际控制逻辑（如调用设备API）
        # cmd = f"CTRL{self._attr_name}: Press\n".encode()

        cmd = ""
        if self._attr_name:
            if self._attr_name.endswith("PowerSync"):
                cmd = "FE010101"
            elif self._attr_name.endswith("CH1_On"):
                cmd = "CF01" + "01" + "01"
            elif self._attr_name.endswith("CH1_Off"):
                cmd = "CF01" + "01" + "02"
            elif self._attr_name.endswith("CH2_On"):
                cmd = "CF01" + "02" + "01"
            elif self._attr_name.endswith("CH2_Off"):
                cmd = "CF01" + "02" + "02"
            elif self._attr_name.endswith("CH3_On"):
                cmd = "CF01" + "03" + "01"
            elif self._attr_name.endswith("CH3_Off"):
                cmd = "CF01" + "03" + "02"
            elif self._attr_name.endswith("CH4_On"):
                cmd = "CF01" + "04" + "01"
            elif self._attr_name.endswith("CH4_Off"):
                cmd = "CF01" + "04" + "02"
            elif self._attr_name.endswith("CH5_On"):
                cmd = "CF01" + "05" + "01"
            elif self._attr_name.endswith("CH5_Off"):
                cmd = "CF01" + "05" + "02"
            elif self._attr_name.endswith("CH6_On"):
                cmd = "CF01" + "06" + "01"
            elif self._attr_name.endswith("CH6_Off"):
                cmd = "CF01" + "06" + "02"
            elif self._attr_name.endswith("CH7_On"):
                cmd = "CF01" + "07" + "01"
            elif self._attr_name.endswith("CH7_Off"):
                cmd = "CF01" + "07" + "02"
            elif self._attr_name.endswith("CH8_On"):
                cmd = "CF01" + "08" + "01"
            elif self._attr_name.endswith("CH8_Off"):
                cmd = "CF01" + "08" + "02"

            try:
                _LOGGER.debug(f"Send cmd: {cmd}")
                # await self._tcp_client.send(cmd)
                # await self._tcp_client.enqueue_data(cmd)
                # _LOGGER.debug(f"Sent cmd: {cmd.decode().strip()}")
            except Exception as err:
                _LOGGER.error(f"Send failed: {err}")
                self._attr_available = False
                self.async_write_ha_state()

        else:
            _LOGGER.warning("self._attr_name is None")
