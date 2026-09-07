"""Constants for the Strava.cz integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "strava_cz"

CONF_CANTEEN_NUMBER = "canteen_number"

DEFAULT_UPDATE_INTERVAL = timedelta(hours=1)
API_TIMEOUT = 60.0

PLATFORMS = [Platform.SENSOR, Platform.SELECT]
