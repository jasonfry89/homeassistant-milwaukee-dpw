import logging
from datetime import timedelta, date
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import (
	CONF_NAME,
	CONF_TYPE,
	CONF_ADDRESS,
	CONF_VALUE_TEMPLATE,
	STATE_UNKNOWN,
)

from homeassistant.helpers.typing import (
	ConfigType,
	DiscoveryInfoType,
	HomeAssistantType,
)

from typing import Any, Callable, Dict, Optional

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=45)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_NAME): cv.string,
	vol.Required(CONF_ADDRESS): cv.string,
	vol.Required(CONF_TYPE): cv.string, 
	vol.Optional(CONF_VALUE_TEMPLATE): cv.template,
})

async def async_setup_platform(
	hass: HomeAssistantType,
	config: ConfigType,
	async_add_entities: Callable,
	discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
	sensors = [MilwaukeeDPWParserSensor(hass, config)]
	async_add_entities(sensors, update_before_add=True)

class MilwaukeeDPWParserSensor(Entity):
	def __init__(self, hass: HomeAssistantType, config: ConfigType):
		super().__init__()
		address = config[CONF_ADDRESS]
		address_parts = address.upper().split(" ")
		self._number = address_parts[0]
		self._direction = address_parts[1]
		self._street = address_parts[2]
		self._suffix = address_parts[3]
		self._collection_type = config[CONF_TYPE].lower()
		self._name = config[CONF_NAME]
		self._state = None
		self._available = True
		self._icon = "mdi:trash-can" if self._collection_type == "garbage" else "mdi:recycle"
		self._value_template = config.get(CONF_VALUE_TEMPLATE)
		if self._value_template is not None:
			self._value_template.hass = hass

	@property
	def name(self) -> str:
		return self._name

	@property
	def available(self) -> bool:
		return self._available

	@property
	def state(self) -> Optional[date]:
		return self._state

	@property
	def icon(self) -> str:
		return self._icon

	async def async_update(self):
		from milwaukee_dpw_parser import get_next_garbage_and_recycling_dates
		garbage_date, recycling_date = await get_next_garbage_and_recycling_dates(
			self._number,
			self._direction,
			self._street,
			self._suffix,
		)
		
		if self._collection_type == "garbage":
			value = garbage_date
		elif self._collection_type == "recycling":
			value = recycling_date
		else:
			raise Exception(f"Invalid collection type {self._collection_type}")
		_LOGGER.debug(f"Value: {value}")

		if self._value_template is not None:
			self._state = self._value_template.render_with_possible_json_value(value, STATE_UNKNOWN)
		else:
			self._state = value
		_LOGGER.debug(f"State: {self._state}")		



