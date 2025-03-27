"""Support for sensor value(s) stored in local files."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_FILE_PATH,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.template import Template

from .const import DEFAULT_NAME, FILE_ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the File++ sensor."""
    config = dict(entry.data)
    options = dict(entry.options)
    file_path: str = config[CONF_FILE_PATH]
    unique_id: str = entry.entry_id
    name: str = config.get(CONF_NAME, DEFAULT_NAME)
    unit: str | None = options.get(CONF_UNIT_OF_MEASUREMENT)
    value_template: Template | None = None

    if CONF_VALUE_TEMPLATE in options:
        value_template = Template(options[CONF_VALUE_TEMPLATE], hass)

    async_add_entities(
        [FileSensor(unique_id, name, file_path, unit, value_template)], True
    )


class FileSensor(SensorEntity):
    """Implementation of a File++ sensor."""

    _attr_icon = FILE_ICON

    def __init__(
        self,
        unique_id: str,
        name: str,
        file_path: str,
        unit_of_measurement: str | None,
        value_template: Template | None,
    ) -> None:
        """Initialize the File++ sensor."""
        self._attr_name = name
        self._file_path = file_path
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._val_tpl = value_template
        self._attr_unique_id = unique_id

        self._file_content = None

    def update(self) -> None:
        """Return entity state."""
        self._attr_native_value = "Ok"

    async def async_update(self):
        """Fetch new state data for the sensor."""

        def get_content():
            try:
                with Path.open(self._file_path, encoding="utf-8") as f:
                    return f.read()
            except (
                IndexError,
                FileNotFoundError,
                IsADirectoryError,
                UnboundLocalError,
            ):
                _LOGGER.warning(
                    "File or data not present at the moment: %s",
                    Path(self._file_path).name,
                )
                return ""

        data = await self.hass.async_add_executor_job(get_content)

        if data and self._val_tpl is not None:
            content = self._val_tpl.async_render_with_possible_json_value(data, None)
        else:
            content = data

        self._file_content = content

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "content": self._file_content,
        }
