"""Support for VeSync humidifiers."""
import logging

# import math
from typing import Optional

from homeassistant.components.humidifier import (
    HumidifierEntity,
    SUPPORT_MODES,
    DEVICE_CLASS_HUMIDIFIER,
)

# from homeassistant.components.fan import (
#     FanEntity,
#     SUPPORT_SET_SPEED,
#     SUPPORT_PRESET_MODE,
# )
# from homeassistant.util.percentage import (
#     int_states_in_range,
#     percentage_to_ranged_value,
#     ranged_value_to_percentage,
# )
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common import VeSyncDevice
from .const import DOMAIN, VS_DISCOVERY, VS_DISPATCHERS, VS_HUMIDIFIERS

_LOGGER = logging.getLogger(__name__)

DEV_TYPE_TO_HA = {
    "Classic300S": "humidifier",
}

MODE_AUTO = "auto"
MODE_NORMAL = "manual"
MODE_SLEEP = "sleep"

PRESET_MODES = [MODE_AUTO, MODE_NORMAL, MODE_SLEEP]
# MIST_LEVEL_RANGE = (1, 9)  # off is not included


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the VeSync humidifier platform."""

    async def async_discover(devices):
        """Add new devices to platform."""
        _async_setup_entities(devices, async_add_entities)

    disp = async_dispatcher_connect(
        hass, VS_DISCOVERY.format(VS_HUMIDIFIERS), async_discover
    )
    hass.data[DOMAIN][VS_DISPATCHERS].append(disp)

    _async_setup_entities(hass.data[DOMAIN][VS_HUMIDIFIERS], async_add_entities)


@callback
def _async_setup_entities(devices, async_add_entities):
    """Check if device is online and add entity."""
    dev_list = []
    for dev in devices:
        if DEV_TYPE_TO_HA.get(dev.device_type) == "humidifier":
            dev_list.append(VeSyncHumidifierHA(dev))
        else:
            _LOGGER.warning(
                "%s - Unknown device type - %s", dev.device_name, dev.device_type
            )
            continue

    async_add_entities(dev_list, update_before_add=True)


class VeSyncHumidifierHA(VeSyncDevice, HumidifierEntity):
    """Representation of a VeSync humidifier."""

    @property
    def is_on(self) -> bool:
        """If the humidifier is currently on or off.

        `self.device.device_status` is always 'on' on this device."""
        return self.device.enabled

    @property
    def target_humidity(self) -> Optional[int]:
        """The target humidity the device is trying to reach."""
        return self.device.config["auto_target_humidity"]

    @property
    def max_humidity(self) -> int:
        """Returns the maximum humidity."""
        return 80

    @property
    def min_humidity(self) -> int:
        """Returns the minimum humidity."""
        return 30

    @property
    def mode(self) -> Optional[str]:
        """The current active preset."""
        if self.device.mode:
            if self.device.mode in self.available_modes:
                return self.device.mode
            _LOGGER.warning("Unsupported humidifier mode %s", self.device.mode)
        return None

    @property
    def available_modes(self) -> list:
        """The available modes."""
        return PRESET_MODES

    # @property
    # def percentage(self) -> Optional[int]:
    #     """
    #     Return the current speed percentage.
    #     Must be a value between 0 (off) and 100.
    #     """
    #     if self.device.mode == "manual":
    #         mist_level = self.device.details["mist_level"]
    #         if mist_level is not None:
    #             return ranged_value_to_percentage(MIST_LEVEL_RANGE, mist_level)
    #     return None

    # @property
    # def speed_count(self) -> int:
    #     """Return the number of speeds the fan supports."""
    #     return int_states_in_range(MIST_LEVEL_RANGE)

    # @property
    # def preset_mode(self) -> Optional[str]:
    #     """Get the current preset mode."""
    #     return self.mode

    # @property
    # def preset_modes(self) -> list:
    #     """Get the list of available preset modes."""
    #     return self.available_modes

    @property
    def supported_features(self):
        """Bitmap of supported features."""
        return SUPPORT_MODES  # | SUPPORT_PRESET_MODE | SUPPORT_SET_SPEED

    @property
    def device_class(self):
        """Device class of the entity."""
        return DEVICE_CLASS_HUMIDIFIER

    @property
    def unique_info(self):
        """Return the ID of this humidifier."""
        return self.device.uuid

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes of the humidifier."""
        details = self.device.details
        # The `humidity` key is reserved for the `target_humdity` by
        # Home Assistant.
        details["current_humidity"] = details.pop("humidity", None)
        return details

    @property
    def entity_picture(self) -> str:
        """Url of a picture to show for the entity."""
        return self.device.device_image

    def set_mode(self, mode: str) -> None:
        """Set new target preset mode."""
        if not self.device.is_on:
            self.device.turn_on()

        if mode in (MODE_AUTO, MODE_SLEEP):
            self.device.set_humidity_mode(mode)
        elif mode == MODE_NORMAL:
            # TODO Add functionality to set mist_level from home assistant.
            self.device.set_mist_level(3)
        else:
            _LOGGER.warning("Unable to set unsupported mode %s", mode)

        self.schedule_update_ha_state()

    def set_humidity(self, humidity: int) -> None:
        """Set new target humidity."""
        self.device.set_humidity(humidity)

    # def set_preset_mode(self, preset_mode: str) -> None:
    #     """Set the preset mode of the fan."""
    #     return self.set_mode(preset_mode)

    # def set_percentage(self, percentage: int) -> None:
    #     """Set the speed percentage of the fan."""
    #     if percentage == 0:
    #         self.device.turn_off()
    #         return

    #     if not self.smartfan.is_on:
    #         self.smartfan.turn_on()

    #     self.device.set_mist_level(
    #         math.ceil(percentage_to_ranged_value(MIST_LEVEL_RANGE, percentage))
    #     )
    #     self.schedule_update_ha_state()

    def turn_on(
        self,
        **kwargs,
    ) -> None:
        """Turn the device on."""
        # _LOGGER.warning("Turn on kwargs: %s", kwargs)
        self.device.turn_on()

        # preset_mode = kwargs.get("preset_mode")
        # if preset_mode:
        #     self.set_mode(preset_mode)
        #     return
        # percentage = kwargs.get("percentage")
        # if percentage:
        #     self.set_percentage(percentage)
