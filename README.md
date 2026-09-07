# Strava.cz for Home Assistant

Custom integration for [Home Assistant](https://www.home-assistant.io/) providing
school canteen data and meal ordering from [Strava.cz](https://app.strava.cz/).

The integration is built on top of the Python library
[`jsem-nerad/strava-cz-python`](https://github.com/jsem-nerad/strava-cz-python),
which provides the Strava.cz API client, menu parsing and ordering logic.

> This repository is the Home Assistant integration layer. It is not affiliated
> with Strava.cz or the upstream `strava-cz-python` project.

## Status

The integration is running successfully on Home Assistant 2026.9.x with a live
Strava.cz account.

Current integration version: **0.1.4**

## Features

- UI setup through Home Assistant Config Flow
- multiple Strava.cz accounts, suitable for multiple children
- account balance
- today's lunch
- tomorrow's lunch
- next ordered lunch
- order a lunch directly from Home Assistant
- cancel an ordered lunch directly from Home Assistant
- meal variants, prices, allergens and deadlines in entity attributes
- coordinator-based polling
- persistent session with automatic re-login after session expiration
- refresh before order changes because Strava.cz meal IDs are not permanent

## Installation

### HACS custom repository

1. Open **HACS**.
2. Add this repository as a **Custom repository** with category **Integration**.
3. Install **Strava.cz**.
4. Restart Home Assistant.
5. Go to **Settings → Devices & services → Add integration**.
6. Search for **Strava.cz**.
7. Enter:
   - Strava.cz username
   - password
   - canteen number

Add the integration once for every Strava.cz account.

### Manual installation

Copy:

```text
custom_components/strava_cz
```

to:

```text
/config/custom_components/strava_cz
```

and restart Home Assistant.

## Entities

Each configured account creates one Home Assistant device with these entities:

- **Balance**
- **Today's lunch**
- **Tomorrow's lunch**
- **Next ordered lunch**
- **Order lunch**
- **Cancel lunch**

## Important API compatibility note

Strava.cz expects the Czech language code **`CZ`** for the login/API requests.
Using `CS` causes the login endpoint to hang until the HTTP client times out.

This behavior was verified against a live Strava.cz account while developing the
Home Assistant integration.

## Upstream project

This integration deliberately delegates Strava.cz API behavior to:

- https://github.com/jsem-nerad/strava-cz-python
- PyPI package: `strava-cz`

The Home Assistant manifest currently pins:

```text
strava-cz==0.4.0
```

Thanks to **Vojtěch Nerad / jsem-nerad** for the Strava.cz Python client and API
research that this integration is based on.

## License

This Home Assistant integration is distributed under the **GPL-3.0-or-later**
license, matching the upstream `strava-cz-python` project.
