# BlueRetro BLE protocol

Reverse-engineered from the official [BlueRetroWebCfg](https://github.com/darthcloud/BlueRetroWebCfg)
web tool. The config interface is only reachable while the adapter is **idle**
(no controller connected); during gameplay the config service is unavailable.

## Service

`56830f56-5180-fab0-314b-2fa176799a00`

## Characteristics (`…a01` … `…a0c`)

| UUID suffix | Name | Access | Meaning |
|-------------|------|--------|---------|
| `…a01` | global config | read/write | system, multitap, inquiry mode, memory card bank (1 byte each) |
| `…a06` | ABI version | read | first byte = ABI int |
| `…a07` | command | write 1 byte, then read | see commands below |
| `…a09` | app / firmware version | read | UTF-8 string |
| `…a0c` | BD address | read | 6 bytes, reversed |

## Commands (written to `…a07`, response read back)

| Byte | Command |
|------|---------|
| `0x04` | get game id (string) |
| `0x05` | get config source (int) |
| `0x07` | get firmware name (string) |
| `0x37` | deep sleep |
| `0x38` | reboot |
| `0x39` | factory reset (destructive) |

## Global config byte layout (`…a01`)

| Byte | Field | Values |
|------|-------|--------|
| 0 | system | `Auto`, `NES`, `SNES`, `N64`, `PSX`, `PS2`, `GC`, `DC`, … (see `SYSTEM_CFG`) |
| 1 | multitap | `None`, `Slot 1`, `Slot 2`, `Dual`, `Alt` |
| 2 | inquiry mode | `Auto`, `Manual` |
| 3 | memory card bank | 0-based byte; reported 1-based (1–4) |

Older firmware sends a shorter payload, so trailing fields may be absent.
Writing the global config requires a reboot to take effect.

> The byte-2 (inquiry) and byte-3 (bank) semantics are inferred from
> `utils/getGlobalCfg.js`; confirm against real hardware.

## Game database

`gameid.db` is a SQLite file (`games(id TEXT, name TEXT)`) bundled from
BlueRetroWebCfg, used to resolve a Game ID to a human-readable name.
