"""Base entities for Strava.cz."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StravaCZCoordinator


class StravaCZEntity(CoordinatorEntity[StravaCZCoordinator]):
    """Base Strava.cz entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: StravaCZCoordinator, child_key: str) -> None:
        super().__init__(coordinator)
        self._entry = coordinator.entry
        self.child_key = child_key

    def make_unique_id(self, suffix: str) -> str:
        """Keep old unique IDs stable for classic accounts."""
        if self.coordinator.is_legacy_single:
            return f"{self._entry.entry_id}_{suffix}"
        return f"{self._entry.entry_id}_{self.child_key}_{suffix}"

    @property
    def child_data(self) -> dict:
        """Return current data for this child."""
        return self.coordinator.child_data(self.child_key)

    @property
    def device_info(self) -> DeviceInfo:
        user = self.child_data.get("user", {})
        title = user.get("full_name") or self._entry.title
        canteen_name = user.get("canteen_name")
        canteen_number = user.get("canteen_number")

        if self.coordinator.is_legacy_single:
            identifier = self._entry.entry_id
        else:
            identifier = f"{self._entry.entry_id}:{self.child_key}"

        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=f"Strava.cz – {title}",
            manufacturer="Strava.cz",
            model=(
                f"Jídelna {canteen_number} • {canteen_name}"
                if canteen_number and canteen_name
                else (f"Jídelna {canteen_number}" if canteen_number else canteen_name)
                or "Školní jídelna"
            ),
            configuration_url="https://app.strava.cz",
        )
