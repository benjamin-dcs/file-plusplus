"""Support for sensor value(s) stored in local files."""

from __future__ import annotations

import logging
import os

from file_read_backwards import FileReadBackwards

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_FILE_PATH,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import Template

from .const import DEFAULT_NAME, FILE_ICON

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
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

    def update(self) -> None:
        """Return entity state."""
        self._attr_native_value = "Ok"

    @property
    def extra_state_attributes(self):
        """
        Return entity state attributes.
        Get the latest entry from a file and updates the state.
        """

        try:
            with open(self._file_path, encoding="utf-8") as f:
                data = f.read()
        except (IndexError, FileNotFoundError, IsADirectoryError, UnboundLocalError) as e:
            _LOGGER.warning(
                "File or data not present at the moment: %s",
                os.path.basename(self._file_path),
            )
            data = ""

        if data and self._val_tpl is not None:
            content = (
                self._val_tpl.async_render_with_possible_json_value(data, None)
            )
        else:
            content = data

        return {
            "content": content,
        }