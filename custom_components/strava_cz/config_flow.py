"""Config flow for Strava.cz."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from strava_cz import AuthenticationError, StravaCZ, StravaError

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import API_TIMEOUT, CONF_CANTEEN_NUMBER, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _validate_input(data: dict[str, Any]) -> dict[str, str]:
    """Validate credentials against Strava.cz."""
    client: StravaCZ | None = None
    try:
        client = StravaCZ(
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            data[CONF_CANTEEN_NUMBER],
            language="CZ",
            timeout=API_TIMEOUT,
        )
        # Login itself is enough to validate credentials. Do not fetch/parse the
        # menu here: individual canteens may expose slightly different menu data,
        # and a parser issue must not make valid credentials look invalid.
        return {
            "title": client.user.full_name or data[CONF_USERNAME],
            "canteen_name": client.user.canteen_name or data[CONF_CANTEEN_NUMBER],
        }
    finally:
        if client is not None:
            try:
                if client.user.is_logged_in:
                    client.logout()
            except StravaError:
                pass
            client.close()


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate user input in the executor."""
    return await hass.async_add_executor_job(_validate_input, data)


class StravaCZConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Strava.cz."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_CANTEEN_NUMBER].strip()}:"
                f"{user_input[CONF_USERNAME].strip().casefold()}"
            )
            await self.async_set_unique_id(unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except StravaError as err:
                _LOGGER.exception("Cannot connect to Strava.cz")
                if "timed out" in str(err).casefold():
                    errors["base"] = "timeout"
                else:
                    errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while validating Strava.cz")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_CANTEEN_NUMBER: user_input[CONF_CANTEEN_NUMBER].strip(),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_CANTEEN_NUMBER): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
