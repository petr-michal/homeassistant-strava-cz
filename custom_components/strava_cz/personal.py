"""Personal-account support for Strava.cz."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from strava_cz import AuthenticationError, StravaCZ
from strava_cz.exceptions import StravaAPIError

from .const import API_TIMEOUT, PERSONAL_S4_FIELDS


@dataclass(frozen=True, slots=True)
class PersonalCanteenAccount:
    """One canteen account linked to a Strava.cz personal account."""

    canteen_number: str
    account_id: str

    @property
    def key(self) -> str:
        """Return a stable key inside one config entry."""
        return f"{self.canteen_number}:{self.account_id}"

    def as_dict(self) -> dict[str, str]:
        """Serialize for Home Assistant config-entry storage."""
        return {
            "canteen_number": self.canteen_number,
            "account_id": self.account_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PersonalCanteenAccount:
        """Build from config-entry data."""
        return cls(
            canteen_number=str(data["canteen_number"]),
            account_id=str(data["account_id"]),
        )


def _mapping(value: Any) -> Mapping[str, Any]:
    """Decode an API value that may itself contain JSON as a string."""
    if isinstance(value, Mapping):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as err:
            raise StravaAPIError("Strava.cz returned invalid JSON") from err
        if isinstance(decoded, Mapping):
            return decoded
    raise StravaAPIError("Strava.cz returned an unexpected response")


def _first(value: Any) -> Any:
    """Take the first value from the API's one-element metadata arrays."""
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def personal_login(client: StravaCZ, email: str, password: str) -> str:
    """Log in with a Strava.cz personal account and return its SID."""
    data = _mapping(
        client._request(  # noqa: SLF001 - upstream has no public PA API yet
            "loginPA",
            {
                "email": email,
                "heslo": password,
                "zustatPrihlasen": False,
                "lang": "CZ",
            },
        )
    )

    result = data.get("Result")
    if isinstance(result, Mapping) and result.get("Status") is False:
        error = result.get("Chyba")
        description = ""
        if isinstance(error, Mapping):
            description = str(error.get("Popis") or "")
        raise AuthenticationError(description or "Přihlášení osobního účtu bylo odmítnuto")

    sid = data.get("SID") or data.get("sid")
    if not sid:
        raise AuthenticationError(
            "Přihlášení osobního účtu nevrátilo session ID",
            payload=data,
        )
    return str(sid)


def personal_accounts(client: StravaCZ, personal_sid: str) -> list[PersonalCanteenAccount]:
    """Return canteen accounts linked to a personal account."""
    data = _mapping(
        client._request(  # noqa: SLF001
            "jidelnyPA",
            {
                "getBeta": True,
                "lang": "CZ",
                "sid": personal_sid,
            },
        )
    )

    raw_accounts = data.get("jidelny")
    if not isinstance(raw_accounts, list):
        return []

    accounts: list[PersonalCanteenAccount] = []
    seen: set[str] = set()
    for raw in raw_accounts:
        if not isinstance(raw, Mapping):
            continue
        canteen_number = str(raw.get("IDJidelny") or raw.get("cislo") or "").strip()
        account_id = str(raw.get("IDUcetJidelny") or raw.get("id") or "").strip()
        if not canteen_number or not account_id:
            continue

        account = PersonalCanteenAccount(canteen_number, account_id)
        if account.key not in seen:
            accounts.append(account)
            seen.add(account.key)

    return accounts


def discover_personal_accounts(
    email: str,
    password: str,
) -> list[PersonalCanteenAccount]:
    """Validate personal credentials and discover linked canteen accounts."""
    client = StravaCZ(language="CZ", timeout=API_TIMEOUT)
    try:
        sid = personal_login(client, email, password)
        return personal_accounts(client, sid)
    finally:
        client.close()


def canteen_login(
    client: StravaCZ,
    personal_sid: str,
    account: PersonalCanteenAccount,
) -> str:
    """Switch a personal session to one linked canteen account."""
    data = client._request(  # noqa: SLF001
        "canteenLoginPA",
        {
            "cislo": account.canteen_number,
            "environment": "W",
            "id": account.account_id,
            "lang": "CZ",
            "sid": personal_sid,
        },
    )

    if not isinstance(data, str) or not data.strip():
        raise AuthenticationError(
            "Strava.cz nevrátilo session ID účtu jídelny",
            payload=data,
        )
    return data.strip().strip('"')


def canteen_s5url(client: StravaCZ, canteen_number: str) -> str:
    """Fetch the S5 endpoint token required by authenticated canteen calls."""
    data = _mapping(
        client._request(  # noqa: SLF001
            "s4Polozky",
            {
                "cislo": canteen_number,
                "lang": "CZ",
                "polozky": PERSONAL_S4_FIELDS,
            },
        )
    )
    s5url = _first(data.get("urlwsdl_s") or data.get("URLWSDL_S"))
    if not s5url:
        raise StravaAPIError(
            f"Jídelna {canteen_number} nevrátila URLWSDL_S"
        )
    return str(s5url)


def canteen_properties(
    client: StravaCZ,
    account: PersonalCanteenAccount,
    canteen_sid: str,
    s5url: str,
) -> Mapping[str, Any]:
    """Load user/account properties after personal-account canteen login."""
    return _mapping(
        client._request(  # noqa: SLF001
            "nactiVlastnostiPA",
            {
                "cislo": account.canteen_number,
                "frontendFunction": "loginCanteenUsingPA",
                "getText": True,
                "checkVersion": True,
                "ignoreCert": False,
                "lang": "CZ",
                "sid": canteen_sid,
                "url": s5url,
            },
        )
    )
