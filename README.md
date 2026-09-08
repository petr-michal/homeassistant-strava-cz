# Strava.cz pro Home Assistant

Custom integrace pro Home Assistant, která zpřístupňuje data ze školních jídelen
používajících Strava.cz.

Integrace vychází z knihovny:
https://github.com/jsem-nerad/strava-cz-python

## Verze 0.2.1

Verze 0.2.1 opravuje popisky výběru přihlášení v Home Assistantu a u zařízení zobrazuje i číslo jídelny.\n\nIntegrace podporuje dva způsoby přihlášení:

### Osobní účet – doporučeno

Přihlášení e-mailem a heslem osobního účtu Strava.cz.

Integrace automaticky načte všechny propojené účty jídelen a každý vytvoří jako
samostatné zařízení v Home Assistantu.

To znamená například:

- Anna – jídelna 0031
- Kryštof – jídelna 0031
- Adéla – jídelna 0176

Stačí jedno přihlášení osobním účtem.

Použitý tok Strava.cz API:

- `loginPA`
- `jidelnyPA`
- `canteenLoginPA`
- `s4Polozky`
- `nactiVlastnostiPA`
- `objednavky`

### Účet jídelny

Původní přihlášení pomocí:

- uživatelského jména
- hesla
- čísla jídelny

zůstává zachováno kvůli zpětné kompatibilitě.

## Entity pro každý účet jídelny

- Zůstatek
- Dnešní oběd
- Zítřejší oběd
- Příští objednaný oběd
- Objednat oběd
- Zrušit oběd

## Důležitá poznámka

Strava.cz používá pro český jazyk v API hodnotu `CZ`. Hodnota `CS` způsobovala
timeout přihlášení a v této integraci se nepoužívá.

## Instalace

Složku:

`custom_components/strava_cz`

zkopíruj do:

`/config/custom_components/strava_cz`

a restartuj Home Assistant.

Pro HACS použij repozitář:

https://github.com/petr-michal/homeassistant-strava-cz

## Licence

GNU GPL v3.0. Integrace používá `strava-cz==0.4.0`.
