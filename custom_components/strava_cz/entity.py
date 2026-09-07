"""Base entities for Strava.cz."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StravaCZCoordinator


class StravaCZEntity(CoordinatorEntity[StravaCZCoordinator]):
    """Base Strava.cz entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StravaCZCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = coordinator.entry

    @property
    def device_info(self) -> DeviceInfo:
        user = self.coordinator.data.get("user", {})
        title = user.get("full_name") or self._entry.title
        canteen_name = user.get("canteen_name")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"Strava.cz – {title}",
            manufacturer="Strava.cz",
            model=canteen_name or "Školní jídelna",
            configuration_url="https://app.strava.cz",
        )
