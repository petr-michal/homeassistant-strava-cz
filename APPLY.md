# Jak změnu aplikovat do GitHub repozitáře

```bash
git clone git@github.com:petr-michal/homeassistant-strava-cz.git
cd homeassistant-strava-cz

# Rozbal ZIP vedle repozitáře a pak překopíruj obsah přes existující soubory:
cp -R /cesta/k/homeassistant-strava-cz-0.2.0-personal-account/. .

git add custom_components/strava_cz README.md
git commit -m "pridat prihlaseni osobnim uctem"
git push
```

Potom aktualizuj integraci v Home Assistantu a restartuj Core.
