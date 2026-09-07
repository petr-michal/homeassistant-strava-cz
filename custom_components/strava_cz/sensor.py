"""Sensors for Strava.cz."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import StravaCZCoordinator
from .entity import StravaCZEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StravaCZCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []

    for child_key in coordinator.child_keys:
        entities.extend(
            [
                StravaCZBalanceSensor(coordinator, child_key),
                StravaCZDaySensor(
                    coordinator, child_key, 0, "Dnešní oběd", "today_lunch"
                ),
                StravaCZDaySensor(
                    coordinator, child_key, 1, "Zítřejší oběd", "tomorrow_lunch"
                ),
                StravaCZNextOrderedSensor(coordinator, child_key),
            ]
        )

    async_add_entities(entities)


def _day_for_offset(
    data: dict[str, Any], offset: int
) -> dict[str, Any] | None:
    wanted = (dt_util.now().date() + timedelta(days=offset)).isoformat()
    return next((day for day in data.get("days", []) if day["date"] == wanted), None)


def _main_meals(day: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not day:
        return []
    return [meal for meal in day.get("meals", []) if meal.get("type") == "main"]


class StravaCZBalanceSensor(StravaCZEntity, SensorEntity):
    """Account balance sensor."""

    _attr_name = "Zůstatek"
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator: StravaCZCoordinator, child_key: str) -> None:
        super().__init__(coordinator, child_key)
        self._attr_unique_id = self.make_unique_id("balance")

    @property
    def native_value(self) -> float | None:
        return self.child_data.get("user", {}).get("balance")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.child_data.get("user", {}).get("currency", "Kč")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        user = self.child_data.get("user", {})
        return {
            "jídelna": user.get("canteen_name"),
            "číslo_jídelny": user.get("canteen_number"),
            "uživatel": user.get("full_name"),
            "účet": user.get("username"),
        }


class StravaCZDaySensor(StravaCZEntity, SensorEntity):
    """Lunch summary for today or tomorrow."""

    _attr_icon = "mdi:food"

    def __init__(
        self,
        coordinator: StravaCZCoordinator,
        child_key: str,
        offset: int,
        name: str,
        unique_suffix: str,
    ) -> None:
        super().__init__(coordinator, child_key)
        self._offset = offset
        self._attr_name = name
        self._attr_unique_id = self.make_unique_id(unique_suffix)

    @property
    def native_value(self) -> str:
        day = _day_for_offset(self.child_data, self._offset)
        meals = _main_meals(day)
        ordered = [meal for meal in meals if meal.get("ordered")]

        if ordered:
            return ordered[0].get("name") or "Objednáno"
        if not day:
            return "Bez jídelníčku"
        if day.get("no_school"):
            return "Nevaří se"
        return "Neobjednáno"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        day = _day_for_offset(self.child_data, self._offset)
        if not day:
            return {}

        meals = _main_meals(day)
        soup = next(
            (meal for meal in day.get("meals", []) if meal.get("type") == "soup"),
            None,
        )

        return {
            "datum": day.get("date"),
            "stav_dne": day.get("status_description"),
            "automatická_objednávka": day.get("auto_ordered"),
            "polévka": soup.get("name") if soup else None,
            "varianty": [
                {
                    "id": meal.get("id"),
                    "varianta": meal.get("variant"),
                    "název": meal.get("name"),
                    "cena": meal.get("price"),
                    "objednáno": meal.get("ordered"),
                    "lze_objednat": meal.get("can_order"),
                    "lze_zrušit": meal.get("can_cancel"),
                    "alergeny": [a.get("code") for a in meal.get("allergens", [])],
                    "uzávěrka": meal.get("deadline"),
                }
                for meal in meals
            ],
        }


class StravaCZNextOrderedSensor(StravaCZEntity, SensorEntity):
    """Next ordered main meal."""

    _attr_name = "Příští objednaný oběd"
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator: StravaCZCoordinator, child_key: str) -> None:
        super().__init__(coordinator, child_key)
        self._attr_unique_id = self.make_unique_id("next_ordered")

    def _next(self) -> dict[str, Any] | None:
        today = dt_util.now().date().isoformat()
        for day in self.child_data.get("days", []):
            if day.get("date", "") < today:
                continue
            for meal in day.get("meals", []):
                if meal.get("type") == "main" and meal.get("ordered"):
                    return meal
        return None

    @property
    def native_value(self) -> str:
        meal = self._next()
        return meal.get("name") if meal else "Nic objednáno"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        meal = self._next()
        if not meal:
            return {}
        return {
            "datum": meal.get("date"),
            "id": meal.get("id"),
            "varianta": meal.get("variant"),
            "cena": meal.get("price"),
        }
