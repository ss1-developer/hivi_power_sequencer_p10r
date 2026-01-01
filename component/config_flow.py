"""Config flow for the HiVi Power Sequencer P10R integration."""

from __future__ import annotations

import logging
from typing import Any
import ipaddress

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiVi Power Sequencer P10R."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input.get(CONF_HOST)
            port = user_input.get(CONF_PORT)

            if not host or not port:
                errors["base"] = "missing_host_port"
            else:
                # 2. 检查IP地址格式
                try:
                    ipaddress.ip_address(host)  # 需要导入 ipaddress
                except ValueError:
                    errors["host"] = "invalid_ip_address"

                # 3. 检查端口范围
                try:
                    port_num = int(port)
                    if not (1 <= port_num <= 65535):
                        errors["port"] = "invalid_port"
                except ValueError:
                    errors["port"] = "invalid_port"

                # 4. 如果没有错误，检查是否重复
                if not errors:
                    # use host:port as unique_id
                    unique_id = f"{host}:{port}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

            if not errors:
                return self.async_create_entry(
                    title=f"HiVi Power Sequencer P10R {unique_id}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=""): str,
                    vol.Required(CONF_PORT, default=8092): int,
                }
            ),
            errors=errors,
        )
