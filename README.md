<p align="center">
  <img src="https://raw.githubusercontent.com/hudsonbrendon/blueretro-ble/main/icons/logo.png" alt="BlueRetro" width="420">
</p>

# blueretro-ble

[![CI](https://github.com/hudsonbrendon/blueretro-ble/actions/workflows/ci.yml/badge.svg)](https://github.com/hudsonbrendon/blueretro-ble/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/blueretro-ble)](https://pypi.org/project/blueretro-ble/)
[![Python](https://img.shields.io/pypi/pyversions/blueretro-ble)](https://pypi.org/project/blueretro-ble/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Talk to a **[BlueRetro](https://github.com/darthcloud/BlueRetro)** retro-console
Bluetooth adapter over Bluetooth LE from Python — read its status and current
game, read and change the global/output config, and reboot or deep-sleep it.

This library powers the
[**BlueRetro Home Assistant integration**](https://github.com/hudsonbrendon/blueretro-homeassistant),
but works standalone in any async Python project (or straight from the command line).

## Features

- 🔌 **Async BLE control** built on [`bleak`](https://github.com/hbldh/bleak) +
  [`bleak-retry-connector`](https://github.com/Bluetooth-Devices/bleak-retry-connector)
  — works on Linux, macOS, and Windows.
- 📊 **Read device state** — firmware, ABI version, BD address, current game id +
  resolved game name, and config source.
- ⚙️ **Read & write config** — system, multitap, pairing mode and memory-card bank
  (global config), plus per-output device mode and accessory.
- 🔁 **Commands** — reboot, deep sleep, and factory reset.
- 🔍 **Discovery helper** — `discover()` finds nearby BlueRetro adapters.
- 🖥️ **CLI** — `blueretro scan / info / reboot / sleep` for quick testing.
- 🏷️ **Bundled game database** — resolves a Game ID to a human-readable name.

## Requirements

- Python **3.11** or newer.
- A Bluetooth LE adapter (built-in or USB).
- A BlueRetro adapter, reachable **only while idle** (no controller connected).

## Installation

```bash
pip install blueretro-ble
```

## CLI usage

```bash
blueretro scan                          # find nearby adapters
blueretro info AA:BB:CC:DD:EE:FF        # connect and print the full state
blueretro reboot AA:BB:CC:DD:EE:FF      # reboot the adapter
blueretro sleep AA:BB:CC:DD:EE:FF       # put the adapter into deep sleep
```

## Library usage

```python
import asyncio
from blueretro_ble import BlueRetroDevice, discover

async def main():
    devices = await discover()
    device = BlueRetroDevice()
    state = await device.async_update(devices[0])
    print(state.fw_version, state.system, state.game_name)

    # change the emulated accessory on output port 1
    await device.async_set_output_config(devices[0], 0, accessory="Memory")

asyncio.run(main())
```

`BlueRetroDevice` methods accept a `bleak` `BLEDevice` (e.g. from Home Assistant's
shared scanner or an ESPHome Bluetooth proxy). `async_update` connects, reads
everything, always disconnects, and never raises — on failure it returns a
`BlueRetroState(available=False)`.

## How it works

BlueRetro exposes a GATT service whose characteristics carry the configuration
and a command channel; `blueretro_ble` reads/decodes them and sends 1-byte
commands.

- Service UUID: `56830f56-5180-fab0-314b-2fa176799a00`
- The configuration is only reachable while the adapter is **idle** (no
  controller paired).
- The protocol is reverse-engineered from the official
  [BlueRetroWebCfg](https://github.com/darthcloud/BlueRetroWebCfg). See
  [`HARDWARE.md`](HARDWARE.md) for the full notes.

## Limitations

- The adapter only accepts connections while **idle** — during gameplay
  `async_update` returns an unavailable state.
- Dreamcast VMU (memory card) transfer needs a large BLE MTU; over stacks stuck
  at MTU 23 it is unreliable — use the official web config for VMU backup/restore.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE) © Hudson Brendon
