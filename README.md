# Sonnenbatterie
Homeassistant integration to show many stats of a Sonnenbatterie. Should work with current versions of Sonnenbatterie.

[![Validate with hassfest](https://github.com/mountain-data/ha_sonnenbatterie/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/mountain-data/ha_sonnenbatterie/actions/workflows/hassfest.yaml)

[![Validate with HACS](https://github.com/mountain-data/ha_sonnenbatterie/actions/workflows/hacs.yml/badge.svg)](https://github.com/mountain-data/ha_sonnenbatterie/actions/workflows/hacs.yml)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)


## Tested working with
* sonnenBatterie 10 performance

## Important: ###
Set the update interval in the Integration Settings. Default is 10 seconds, I use 2 s. Might put a high load in the DB

If you feel that your Sonnenbatterie **should** provide one or more of those
you can enable the "debug_mode" from

_Settings -> Devices & Services -> Integrations -> Sonnenbatterie_

Just enable the "Debug mode" and restart your HomeAssistant instance. You'll get
the full data that's returned by your Sonnenbatterie in the logs. Please put those
logs along with the setting you want monitored into a new issue.

## Install
Easiest way is to add this repository to hacs as a custom repository.
