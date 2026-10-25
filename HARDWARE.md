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

## Memory-card transfer (`…a0a` / `…a0b`)

One flat 128 KiB buffer (32 × 4 KiB blocks): the whole Dreamcast VMU, or four
32 KiB N64 Controller Pak banks. Write a uint32 byte offset to `…a0a`, then read
or write `…a0b` repeatedly; finish by writing `0` to `…a0a`.

Verified in the shipped v25.04 Dreamcast binary (Ghidra via REA; `mc_offset`
@ `0x3ffc933c`, `mtu` @ `0x3ffbe06a`, read handler `0x400de9d4`, ATT handler
`0x400dea28`):

- **One global cursor**, auto-advanced by every data read/write and only set by
  writes to `…a0a`. Resuming a dropped transfer = writing the offset again.
- A **read** returns `min(bytes left in the 4 KiB block, (mtu - 2) & ~3)`, so
  the first chunk length reveals the negotiated MTU. Reads never return empty.
- The **MTU is a global** too: set by each MTU exchange and never reset on
  disconnect.
- A write longer than one ATT packet turns into prepare/execute writes, and
  **every execute rewrites the config file to flash** (`config_update`) unless
  an OTA is running. Size data writes to a single Write Request instead.
- Writes reach flash asynchronously: 1 s after the last write, then one 4 KiB
  block every 20 ms (`mc_store_spread`). Wait a few seconds before power-off.
- **VMU byte order:** the buffer holds Maple bus words, each 32-bit word
  byte-reversed versus a standard VMU `.bin` (the web config swaps both ways).
  N64 paks are stored as-is.

## Advertising and connection parameters

- Advertises connectable `ADV_IND` every 100 ms (interval `0xA0`) while idle.
  Advertising stops when any Bluetooth controller connects and resumes only
  after the last one disconnects (`hci.c`), so "no advertisements" = in use
  (or powered off).
- The first **read** of `…a07` asks the central for a 7.5-15 ms connection
  interval (supervision timeout 9.6 s). macOS showed ~105 ms per read either way.
- Game IDs come from the console only on N64, GameCube (SI) and PS1/PS2 (SPI);
  other systems report the system name (e.g. `DC`) set at boot.

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
