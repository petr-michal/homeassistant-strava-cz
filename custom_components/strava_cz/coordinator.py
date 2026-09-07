"""Data coordinator for Strava.cz."""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from strava_cz import AuthenticationError, StravaCZ, StravaError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_TIMEOUT, CONF_CANTEEN_NUMBER, DEFAULT_UPDATE_INTERVAL, DOMAIN


class StravaCZCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate one Strava.cz account."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=f"{DOMAIN}:{entry.entry_id}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.entry = entry
        self._client: StravaCZ | None = None
        self._io_lock = asyncio.Lock()

    def _new_client(self) -> StravaCZ:
        return StravaCZ(
            self.entry.data[CONF_USERNAME],
            self.entry.data[CONF_PASSWORD],
            self.entry.data[CONF_CANTEEN_NUMBER],
            language="CZ",
            timeout=API_TIMEOUT,
        )

    def _close_client_sync(self) -> None:
        if self._client is None:
            return
        with contextlib.suppress(StravaError):
            if self._client.user.is_logged_in:
                self._client.logout()
        self._client.close()
        self._client = None

    def _ensure_client_sync(self) -> StravaCZ:
        if self._client is None:
            self._client = self._new_client()
        return self._client

    def _fetch_sync(self) -> dict[str, Any]:
        client = self._ensure_client_sync()
        try:
            client.menu.fetch()
        except AuthenticationError:
            self._close_client_sync()
            client = self._ensure_client_sync()
            client.menu.fetch()
        return self._snapshot(client)

    @staticmethod
    def _snapshot(client: StravaCZ) -> dict[str, Any]:
        user = client.user
        days: list[dict[str, Any]] = []

        for day in client.menu.days:
            meals: list[dict[str, Any]] = []
            for meal in day.meals:
                meals.append(
                    {
                        "id": meal.id,
                        "date": meal.date.isoformat(),
                        "type": meal.type.value,
                        "variant": meal.variant,
                        "name": meal.name,
                        "price": meal.price,
                        "ordered": meal.ordered,
                        "can_order": meal.can_order,
                        "can_cancel": meal.can_cancel,
                        "order_restriction": meal.order_restriction.description,
                        "cancel_restriction": meal.cancel_restriction.description,
                        "allergens": [
                            {"code": allergen.code, "name": allergen.name}
                            for allergen in meal.allergens
                        ],
                        "deadline": (
                            meal.deadline.isoformat() if meal.deadline is not None else None
                        ),
                    }
                )

            days.append(
                {
                    "date": day.date.isoformat(),
                    "status": day.status.value,
                    "status_description": day.status.description,
                    "auto_ordered": day.auto_ordered,
                    "ordered": day.ordered,
                    "no_school": day.no_school,
                    "meals": meals,
                }
            )

        return {
            "user": {
                "username": user.username,
                "full_name": user.full_name,
                "balance": user.balance,
                "currency": user.currency,
                "canteen_number": user.canteen_number,
                "canteen_name": user.canteen_name,
            },
            "days": days,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        async with self._io_lock:
            try:
                return await self.hass.async_add_executor_job(self._fetch_sync)
            except AuthenticationError as err:
                raise ConfigEntryAuthFailed("Strava.cz authentication failed") from err
            except StravaError as err:
                raise UpdateFailed(f"Strava.cz update failed: {err}") from err

    def _change_meal_sync(self, meal_id: int, ordered: bool) -> dict[str, Any]:
        for attempt in range(2):
            client = self._ensure_client_sync()
            try:
                client.menu.fetch()

                if ordered:
                    client.menu.order_meals(meal_id)
                else:
                    client.menu.cancel_meals(meal_id)

                return self._snapshot(client)
            except AuthenticationError:
                self._close_client_sync()
                if attempt:
                    raise

        raise AuthenticationError("Strava.cz authentication failed")

    async def async_change_meal(self, meal_id: int, ordered: bool) -> None:
        """Order or cancel a meal and publish the new coordinator data."""
        async with self._io_lock:
            try:
                data = await self.hass.async_add_executor_job(
                    self._change_meal_sync, int(meal_id), ordered
                )
            except AuthenticationError as err:
                raise ConfigEntryAuthFailed("Strava.cz authentication failed") from err
            except StravaError as err:
                raise HomeAssistantError(str(err)) from err

            self.async_set_updated_data(data)

    async def async_close(self) -> None:
        """Close the remote session and HTTP client."""
        async with self._io_lock:
            await self.hass.async_add_executor_job(self._close_client_sync)
