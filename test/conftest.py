"""Common fixtures for the HiVi Power Sequencer P10R tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.hivi_power_sequencer_p10r.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry
