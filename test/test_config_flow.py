"""Test the HiVi Power Sequencer P10R config flow."""

from unittest.mock import AsyncMock, patch
import pytest

from homeassistant import config_entries
from homeassistant.components.hivi_power_sequencer_p10r.config_flow import (
    CannotConnect,
    InvalidAuth,
)
from homeassistant.components.hivi_power_sequencer_p10r.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


class TestConfigFlow:
    """Test the HiVi Power Sequencer P10R config flow."""

    @pytest.fixture(autouse=True)
    def mock_setup_entry(self) -> AsyncMock:
        """Mock the setup_entry method."""
        with patch(
            "homeassistant.components.hivi_power_sequencer_p10r.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry:
            yield mock_setup_entry

    async def test_flow_user_step_form(self, hass: HomeAssistant) -> None:
        """Test the initial step shows the form with correct fields."""
        # 初始化流程
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # 验证显示表单
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        # 验证表单字段
        schema = result["data_schema"].schema
        assert CONF_HOST in schema
        assert CONF_PORT in schema

        # 验证默认值
        data_schema = result["data_schema"]
        assert data_schema({})[CONF_HOST] == ""
        assert data_schema({})[CONF_PORT] == 8092

    async def test_flow_with_valid_input_creates_entry(
        self, hass: HomeAssistant, mock_setup_entry: AsyncMock
    ) -> None:
        """Test that valid input creates an entry."""
        # 初始化流程
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # 提交有效数据
        test_data = {
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 8092,
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=test_data,
        )

        # 验证创建了配置项
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert (
            result["title"]
            == f"HiVi Power Sequencer P10R {test_data.get(CONF_HOST, 'Unknown')}:{test_data.get(CONF_PORT, 'Unknown')}"
        )
        assert result["data"] == test_data

        # 验证 unique_id 设置正确
        assert (
            result["result"].unique_id
            == f"{test_data[CONF_HOST]}:{test_data[CONF_PORT]}"
        )

        # 验证 setup_entry 被调用
        mock_setup_entry.assert_called_once()

    async def test_flow_missing_host_shows_error(self, hass: HomeAssistant) -> None:
        """Test that missing host shows error."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        # 提交缺失 host 的数据
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "", CONF_PORT: 8092},  # 空的 host
        )

        # 验证显示错误
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "missing_host_port"

        # 验证错误后表单保留输入的值
        data_schema = result["data_schema"]
        assert data_schema({})[CONF_PORT] == 8092  # 端口默认值保留
        # 注意：host 应该是空字符串，因为验证失败了


# async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
#     """Test we get the form."""
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )

#     print(f"result = {result}")

#     assert result["type"] is FlowResultType.FORM
#     assert result["errors"] == {}

#     with patch(
#         "homeassistant.components.hivi_power_sequencer_p10r.config_flow.PlaceholderHub.authenticate",
#         return_value=True,
#     ):
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             {
#                 CONF_HOST: "1.1.1.1",
#                 CONF_USERNAME: "test-username",
#                 CONF_PASSWORD: "test-password",
#             },
#         )
#         await hass.async_block_till_done()

# assert result["type"] is FlowResultType.CREATE_ENTRY
# assert result["title"] == "Name of the device"
# assert result["data"] == {
#     CONF_HOST: "1.1.1.1",
#     CONF_USERNAME: "test-username",
#     CONF_PASSWORD: "test-password",
# }
# assert len(mock_setup_entry.mock_calls) == 1


# async def test_form_invalid_auth(
#     hass: HomeAssistant, mock_setup_entry: AsyncMock
# ) -> None:
#     """Test we handle invalid auth."""
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )

#     with patch(
#         "homeassistant.components.hivi_power_sequencer_p10r.config_flow.PlaceholderHub.authenticate",
#         side_effect=InvalidAuth,
#     ):
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             {
#                 CONF_HOST: "1.1.1.1",
#                 CONF_USERNAME: "test-username",
#                 CONF_PASSWORD: "test-password",
#             },
#         )

#     assert result["type"] is FlowResultType.FORM
#     assert result["errors"] == {"base": "invalid_auth"}

#     # Make sure the config flow tests finish with either an
#     # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
#     # we can show the config flow is able to recover from an error.
#     with patch(
#         "homeassistant.components.hivi_power_sequencer_p10r.config_flow.PlaceholderHub.authenticate",
#         return_value=True,
#     ):
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             {
#                 CONF_HOST: "1.1.1.1",
#                 CONF_USERNAME: "test-username",
#                 CONF_PASSWORD: "test-password",
#             },
#         )
#         await hass.async_block_till_done()

#     assert result["type"] is FlowResultType.CREATE_ENTRY
#     assert result["title"] == "Name of the device"
#     assert result["data"] == {
#         CONF_HOST: "1.1.1.1",
#         CONF_USERNAME: "test-username",
#         CONF_PASSWORD: "test-password",
#     }
#     assert len(mock_setup_entry.mock_calls) == 1


# async def test_form_cannot_connect(
#     hass: HomeAssistant, mock_setup_entry: AsyncMock
# ) -> None:
#     """Test we handle cannot connect error."""
#     result = await hass.config_entries.flow.async_init(
#         DOMAIN, context={"source": config_entries.SOURCE_USER}
#     )

#     with patch(
#         "homeassistant.components.hivi_power_sequencer_p10r.config_flow.PlaceholderHub.authenticate",
#         side_effect=CannotConnect,
#     ):
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             {
#                 CONF_HOST: "1.1.1.1",
#                 CONF_USERNAME: "test-username",
#                 CONF_PASSWORD: "test-password",
#             },
#         )

#     assert result["type"] is FlowResultType.FORM
#     assert result["errors"] == {"base": "cannot_connect"}

#     # Make sure the config flow tests finish with either an
#     # FlowResultType.CREATE_ENTRY or FlowResultType.ABORT so
#     # we can show the config flow is able to recover from an error.

#     with patch(
#         "homeassistant.components.hivi_power_sequencer_p10r.config_flow.PlaceholderHub.authenticate",
#         return_value=True,
#     ):
#         result = await hass.config_entries.flow.async_configure(
#             result["flow_id"],
#             {
#                 CONF_HOST: "1.1.1.1",
#                 CONF_USERNAME: "test-username",
#                 CONF_PASSWORD: "test-password",
#             },
#         )
#         await hass.async_block_till_done()

#     assert result["type"] is FlowResultType.CREATE_ENTRY
#     assert result["title"] == "Name of the device"
#     assert result["data"] == {
#         CONF_HOST: "1.1.1.1",
#         CONF_USERNAME: "test-username",
#         CONF_PASSWORD: "test-password",
#     }
#     assert len(mock_setup_entry.mock_calls) == 1
