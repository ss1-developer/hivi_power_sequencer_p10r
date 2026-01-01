# custom_components/ss-power-sequencer-p10r/switch.py
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
import voluptuous as vol
from homeassistant.helpers.entity import Entity
import logging
from homeassistant.components.button import ButtonEntity
from .tcp_client import TCPClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ss-power-sequencer-p10r"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    """实体平台设置"""
    # platform = entity_platform.async_get_current_platform()

    tcp_client = hass.data[DOMAIN][entry.entry_id]["tcp_client"]
    device_id = hass.data[DOMAIN][entry.entry_id]["device_id"]

    ip = entry.data["ip"]
    _LOGGER.debug(f"ip = {ip}")
    port = entry.data["port"]
    _LOGGER.debug(f"port = {port}")

    _LOGGER.debug(f"button async_setup_entry ip = {ip}")
    _LOGGER.debug(f"button async_setup_entry port = {port}")
    _LOGGER.debug(f"button async_setup_entry tcp_client.ip_addr = {tcp_client.ip_addr}")
    _LOGGER.debug(f"button async_setup_entry tcp_client.port = {tcp_client.port}")

    btn_idx = 1
    btn_name = "PowerOn1"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 2
    btn_name = "PowerOff1"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 3
    btn_name = "PowerOn2"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 4
    btn_name = "PowerOff2"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 5
    btn_name = "PowerOn3"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 6
    btn_name = "PowerOff3"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 7
    btn_name = "PowerOn4"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 8
    btn_name = "PowerOff4"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 9
    btn_name = "PowerOn5"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 10
    btn_name = "PowerOff5"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 11
    btn_name = "PowerOn6"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 12
    btn_name = "PowerOff6"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 13
    btn_name = "PowerOn7"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 14
    btn_name = "PowerOff7"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 15
    btn_name = "PowerOn8"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 16
    btn_name = "PowerOff8"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    btn_idx = 17
    btn_name = "PowerSync"
    buttons = [
        PowerSequencerButton(
            entry, ip, port, entry.entry_id, btn_idx, btn_name, tcp_client=tcp_client
        )
    ]
    async_add_entities(buttons)

    # # 监听TCP数据事件（可选）
    # async def handle_received_data(event):
    #     _LOGGER.info(f"处理接收数据: {event.data}")

    # hass.bus.async_listen(f"{DOMAIN}_data_received", handle_received_data)

    return True


class PowerSequencerButton(ButtonEntity):
    """代表电源时序器的虚拟实体"""

    def __init__(
        self, entry, ip, port, entry_id, btn_idx, btn_name, tcp_client: TCPClient
    ):
        device_identifiers = {(DOMAIN, f"power_sequencer_p10r_{ip}_{port}_{entry_id}")}
        self._entry = entry
        self._attr_device_info = {"identifiers": device_identifiers}
        self._attr_unique_id = f"power_sequencer_p10r_{ip}_{port}_{entry_id}_{btn_name}"
        # self._attr_name = f"{ip}_{port}_{btn_name}"
        self._attr_name = f"{btn_name}"
        self._attr_entity_id = f"button.power_sequencer_p10r_{ip}_{port}_{btn_name.lower().replace(' ', '_')}"
        self._tcp_client = tcp_client

    async def async_press(self) -> None:
        """按钮按下时的处理逻辑"""
        _LOGGER.info(f"{self._attr_name} press")
        # 这里实现实际控制逻辑（如调用设备API）
        # cmd = f"CTRL{self._attr_name}: Press\n".encode()

        cmd = ""
        if self._attr_name.endswith("PowerSync"):
            cmd = "FE010101"
        elif self._attr_name.endswith("PowerOn1"):
            cmd = "CF01" + "01" + "01"
        elif self._attr_name.endswith("PowerOff1"):
            cmd = "CF01" + "01" + "02"
        elif self._attr_name.endswith("PowerOn2"):
            cmd = "CF01" + "02" + "01"
        elif self._attr_name.endswith("PowerOff2"):
            cmd = "CF01" + "02" + "02"
        elif self._attr_name.endswith("PowerOn3"):
            cmd = "CF01" + "03" + "01"
        elif self._attr_name.endswith("PowerOff3"):
            cmd = "CF01" + "03" + "02"
        elif self._attr_name.endswith("PowerOn4"):
            cmd = "CF01" + "04" + "01"
        elif self._attr_name.endswith("PowerOff4"):
            cmd = "CF01" + "04" + "02"
        elif self._attr_name.endswith("PowerOn5"):
            cmd = "CF01" + "05" + "01"
        elif self._attr_name.endswith("PowerOff5"):
            cmd = "CF01" + "05" + "02"
        elif self._attr_name.endswith("PowerOn6"):
            cmd = "CF01" + "06" + "01"
        elif self._attr_name.endswith("PowerOff6"):
            cmd = "CF01" + "06" + "02"
        elif self._attr_name.endswith("PowerOn7"):
            cmd = "CF01" + "07" + "01"
        elif self._attr_name.endswith("PowerOff7"):
            cmd = "CF01" + "07" + "02"
        elif self._attr_name.endswith("PowerOn8"):
            cmd = "CF01" + "08" + "01"
        elif self._attr_name.endswith("PowerOff8"):
            cmd = "CF01" + "08" + "02"

        try:
            _LOGGER.debug(f"Send cmd: {cmd}")
            # await self._tcp_client.send(cmd)
            await self._tcp_client.enqueue_data(cmd)
            # _LOGGER.debug(f"Sent cmd: {cmd.decode().strip()}")
        except Exception as err:
            _LOGGER.error(f"Send failed: {err}")
            self._attr_available = False
            self.async_write_ha_state()
