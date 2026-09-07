# Strava.cz pro Home Assistant

Custom integrace pro [Home Assistant](https://www.home-assistant.io/), která zpřístupňuje
data ze školních jídelen používajících [Strava.cz](https://app.strava.cz/).

Integrace je postavená nad Python knihovnou
[`jsem-nerad/strava-cz-python`](https://github.com/jsem-nerad/strava-cz-python),
která zajišťuje komunikaci se Strava.cz API, načítání jídelníčku a objednávání jídel.

> Tento repozitář obsahuje Home Assistant integrační vrstvu. Není oficiálně spojen
> se Strava.cz ani s upstream projektem `strava-cz-python`.

## Stav

Integrace je funkční a ověřená na Home Assistant 2026.9.x proti reálnému účtu Strava.cz.

Aktuální verze integrace: **0.1.4**

## Funkce

- nastavení přes UI pomocí Home Assistant Config Flow
- podpora více účtů, vhodné například pro více dětí
- zůstatek na účtu
- dnešní oběd
- zítřejší oběd
- příští objednaný oběd
- objednání oběda přímo z Home Assistantu
- zrušení objednaného oběda přímo z Home Assistantu
- varianty jídel, ceny, alergeny a termíny objednávek v atributech entit
- pravidelné načítání dat přes DataUpdateCoordinator
- udržování přihlášené session
- automatické nové přihlášení po expiraci session
- obnovení jídelníčku před změnou objednávky, protože ID jídel na Strava.cz nejsou trvalá

## Instalace

### Přes HACS jako vlastní repozitář

1. Otevři **HACS**.
2. Přidej tento repozitář jako **Vlastní repozitář / Custom repository**.
3. Jako kategorii zvol **Integrace / Integration**.
4. Nainstaluj **Strava.cz**.
5. Restartuj Home Assistant.
6. Otevři **Nastavení → Zařízení a služby → Přidat integraci**.
7. Vyhledej **Strava.cz**.
8. Zadej:
   - uživatelské jméno
   - heslo
   - číslo jídelny

Pro každý další účet Strava.cz přidej integraci znovu.

### Ruční instalace

Zkopíruj složku:

```text
custom_components/strava_cz
```

do:

```text
/config/custom_components/strava_cz
```

a restartuj Home Assistant.

## Vytvářené entity

Každý nakonfigurovaný účet vytvoří jedno zařízení Strava.cz a tyto entity:

- **Zůstatek**
- **Dnešní oběd**
- **Zítřejší oběd**
- **Příští objednaný oběd**
- **Objednat oběd**
- **Zrušit oběd**

Díky tomu je možné mít v jednom Home Assistantu několik samostatných účtů, například
pro více dětí.

## Objednávání jídel

Entita **Objednat oběd** nabízí pouze hlavní jídla, která je možné v danou chvíli
objednat.

Entita **Zrušit oběd** nabízí pouze objednaná jídla, která je ještě možné zrušit.

Před změnou objednávky integrace znovu načte aktuální jídelníček, protože identifikátory
jídel na Strava.cz se mohou změnit.

## Důležitá poznámka k API

Strava.cz očekává pro český jazyk v API hodnotu:

```text
CZ
```

Použití hodnoty `CS` způsobuje, že požadavek na přihlášení může zůstat viset až do
HTTP timeoutu.

Toto chování bylo při vývoji integrace ověřeno proti reálnému účtu Strava.cz.

## Použitá knihovna

Integrace používá:

- [jsem-nerad/strava-cz-python](https://github.com/jsem-nerad/strava-cz-python)
- PyPI balíček `strava-cz`

V Home Assistant manifestu je aktuálně použita verze:

```text
strava-cz==0.4.0
```

Velké poděkování patří autorovi **Vojtěchu Neradovi / jsem-nerad** za Python klienta
a zdokumentování Strava.cz API, ze kterého tato integrace vychází.

## Kompatibilita

Aktuálně ověřeno na:

- Home Assistant Core **2026.9.x**
- `strava-cz==0.4.0`

## Licence

Projekt je distribuován pod licencí **GNU GPL v3.0**.

Viz soubor [LICENSE](LICENSE).
