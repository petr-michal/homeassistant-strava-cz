"""Config flow for Strava.cz."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from strava_cz import AuthenticationError, StravaCZ, StravaError

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import (
    ACCOUNT_TYPE_CANTEEN,
    ACCOUNT_TYPE_PERSONAL,
    API_TIMEOUT,
    CONF_ACCOUNT_TYPE,
    CONF_ACCOUNTS,
    CONF_CANTEEN_NUMBER,
    DOMAIN,
)
from .personal import discover_personal_accounts

_LOGGER = logging.getLogger(__name__)


def _validate_canteen_input(data: dict[str, Any]) -> dict[str, str]:
    """Validate classic canteen credentials against Strava.cz."""
    client: StravaCZ | None = None
    try:
        client = StravaCZ(
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            data[CONF_CANTEEN_NUMBER],
            language="CZ",
            timeout=API_TIMEOUT,
        )
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


async def validate_canteen_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, str]:
    """Validate classic user input in the executor."""
    return await hass.async_add_executor_job(_validate_canteen_input, data)


async def validate_personal_input(
    hass: HomeAssistant, email: str, password: str
) -> list[dict[str, str]]:
    """Validate personal credentials and return linked account metadata."""
    accounts = await hass.async_add_executor_job(
        discover_personal_accounts,
        email,
        password,
    )
    return [account.as_dict() for account in accounts]


class StravaCZConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Strava.cz."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Let the user choose the login type."""
        return self.async_show_menu(
            step_id="user",
            menu_options={
                ACCOUNT_TYPE_PERSONAL: "Osobní účet (doporučeno)",
                ACCOUNT_TYPE_CANTEEN: "Účet jídelny",
            },
        )

    async def async_step_personal(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure a Strava.cz personal account."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            await self.async_set_unique_id(
                f"personal:{email.casefold()}",
                raise_on_progress=False,
            )
            self._abort_if_unique_id_configured()

            try:
                accounts = await validate_personal_input(
                    self.hass,
                    email,
                    user_input[CONF_PASSWORD],
                )
                if not accounts:
                    errors["base"] = "no_accounts"
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except StravaError as err:
                _LOGGER.exception("Cannot connect personal Strava.cz account")
                errors["base"] = (
                    "timeout" if "timed out" in str(err).casefold() else "cannot_connect"
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Strava.cz personal account")
                errors["base"] = "unknown"
            else:
                if accounts:
                    return self.async_create_entry(
                        title=email,
                        data={
                            CONF_ACCOUNT_TYPE: ACCOUNT_TYPE_PERSONAL,
                            CONF_EMAIL: email,
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_ACCOUNTS: accounts,
                        },
                    )

        return self.async_show_form(
            step_id="personal",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_canteen(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure a classic canteen account."""
        errors: dict[str, str] = {}

        if user_input is not None:
            unique_id = (
                f"{user_input[CONF_CANTEEN_NUMBER].strip()}:"
                f"{user_input[CONF_USERNAME].strip().casefold()}"
            )
            await self.async_set_unique_id(unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_canteen_input(self.hass, user_input)
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except StravaError as err:
                _LOGGER.exception("Cannot connect to Strava.cz")
                errors["base"] = (
                    "timeout" if "timed out" in str(err).casefold() else "cannot_connect"
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error while validating Strava.cz")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_ACCOUNT_TYPE: ACCOUNT_TYPE_CANTEEN,
                        CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_CANTEEN_NUMBER: user_input[CONF_CANTEEN_NUMBER].strip(),
                    },
                )

        return self.async_show_form(
            step_id="canteen",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_CANTEEN_NUMBER): str,
                }
            ),
            errors=errors,
        )
