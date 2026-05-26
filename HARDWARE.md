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
| `…a02` | output control | write | uint16 output/port index to select |
| `…a03` | output config | read/write | `[device, accessory]` for the selected output |
| `…a06` | ABI version | read | first byte = ABI int |
| `…a07` | command | write 1 byte, then read | see commands below |
| `…a09` | app / firmware version | read | UTF-8 string |
| `…a0a` | file control | write | uint32 offset (reset to 0 around a transfer) |
| `…a0b` | file data | read/write | chunked file payload (e.g. Dreamcast VMU) |
| `…a0c` | BD address | read | 6 bytes, reversed |

## Per-output config (`…a03`)

Select the output by writing its uint16 index to `…a02`, then read/write 2 bytes
on `…a03`:

| Byte | Field | Values |
|------|-------|--------|
| 0 | device mode | `GamePad`, `GamePadAlt`, `Keyboard`, `Mouse` |
| 1 | accessory | `None`, `Memory` (VMU), `Rumble` (Jump Pack), `Both` |

Up to 12 outputs. On Dreamcast each output maps to a port; only one output may
use `Memory`/`Both` (a single emulated VMU).

## Dreamcast VMU transfer (`…a0a` / `…a0b`)

The emulated VMU is a 128 KiB image. Reset the cursor by writing a uint32 `0` to
`…a0a`, then read `…a0b` repeatedly (each read returns an MTU-sized chunk) until
128 KiB are collected (write chunks the same way), then reset the cursor to `0`.

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
