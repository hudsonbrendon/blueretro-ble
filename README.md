<p align="center">
  <img src="https://raw.githubusercontent.com/hudsonbrendon/blueretro-ble/main/icons/logo.png" alt="BlueRetro" width="360">
</p>

# blueretro-ble

[![Tests](https://github.com/hudsonbrendon/blueretro-ble/actions/workflows/test.yml/badge.svg)](https://github.com/hudsonbrendon/blueretro-ble/actions/workflows/test.yml)
[![PyPI](https://img.shields.io/pypi/v/blueretro-ble.svg)](https://pypi.org/project/blueretro-ble/)
[![Python](https://img.shields.io/pypi/pyversions/blueretro-ble.svg)](https://pypi.org/project/blueretro-ble/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Pure-Python BLE library for the [BlueRetro](https://github.com/darthcloud/BlueRetro)
retro-console Bluetooth adapter. Talks to the BlueRetro GATT server via
[`bleak`](https://github.com/hbldh/bleak) +
[`bleak-retry-connector`](https://github.com/Bluetooth-Devices/bleak-retry-connector)
(connect → read/write → disconnect).

Powers the [BlueRetro Home Assistant integration](https://github.com/hudsonbrendon/blueretro-homeassistant).

## Install

```bash
pip install blueretro-ble
```

## Usage

```python
from blueretro_ble import BlueRetroDevice, supports

# `supports(advertisement)` is a discovery predicate: True if a BLE
# advertisement (anything exposing `.name` and `.service_uuids`) looks
# like a BlueRetro adapter.

device = BlueRetroDevice()
state = await device.async_update(ble_device)  # a bleak BLEDevice
print(state.fw_version, state.game_id, state.game_name)

await device.async_reboot(ble_device)
await device.async_deep_sleep(ble_device)
```

`async_update` connects, reads ABI/firmware/BD-address directly, runs two
command-then-read cycles (game id, config source), resolves the game name from
the bundled `gameid.db`, always disconnects, and never raises — on failure it
returns a `BlueRetroState(available=False)`.

## Notes

- The adapter only accepts connections while **idle** (no controller connected).
  During gameplay, connections fail and `async_update` returns an unavailable state.
- `gameid.db` is a SQLite database (`games(id TEXT, name TEXT)`) bundled with the
  package, sourced from `darthcloud/BlueRetroWebCfg`.
- The BLE protocol is reverse-engineered from the official web config; verify
  `cfg_src` (`0x05`) against real hardware.

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
```

## License

MIT
