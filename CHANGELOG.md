# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.0] - 2026-05-29

### Added
- **Memory-card writes & N64 Controller Pak.** `async_write_vmu` (128 KiB),
  `async_read_pak` / `async_write_pak` / `async_format_pak` (32 KiB banks 0–3).
  Writes are block-aligned (never cross a 4 KiB boundary) per firmware
  requirement. `make_formatted_pak()` generates a blank, valid pak image (ported
  from BlueRetroWebCfg / bryc's MPKEdit).
- **Config files manager.** `async_list_files` and `async_delete_file` over the
  command characteristic.
- **OTA firmware update.** `async_ota_update(firmware, progress=...)` streams a
  `BlueRetro_*.bin` image and reboots into it, aborting cleanly on error.
- **Advanced input mapping.** `InputMapping` model plus `async_read_input_config`
  / `async_write_input_config`, and pure `encode_input_config` /
  `decode_input_config` (8-byte entries: src/dest/dest_id/max/threshold/deadzone/
  turbo/scaling+diag).
- New constants/UUIDs: `CHAR_IN_CFG_CTRL/DATA`, `CHAR_OTA_FW_DATA`, file/dir/OTA
  command opcodes, `PAK_SIZE`, `PAK_BANKS`, `MC_BLOCK`, `IN_CFG_CHUNK`.

### Note
- Large transfers (VMU/pak/OTA) require a large negotiated MTU. They work over a
  desktop browser stack (MTU 517) but may fail over Linux/BlueZ (MTU 23) — the
  same limitation that affects VMU backup.

## [0.6.0] - 2026-05-29

### Added
- **Multi-port output config.** `BlueRetroState.ports` now holds a
  `{port: (device, accessory)}` mapping. `async_update(ble_device, output_ports=N)`
  reads the first `N` ports (clamped to `1..MAX_OUTPUT`) in a single connection;
  port 0 still mirrors into `controller_mode` / `accessory` for backward
  compatibility (default `output_ports=1` keeps the previous behavior).
- **`async_read_outputs(ble_device, ports=N)`** — read several ports' output
  configs in one connection, returning a `{port: (device, accessory)}` mapping.

## [0.5.0] - 2026-05-28

### Added
- `parse_firmware()` — split the adapter firmware string into
  `(sw_version, hw_version, platform)`. (Moved here from the HA integration so all
  BlueRetro logic lives in the library.)

### Changed
- README rewritten to the standard library layout.

## [0.4.0] - 2026-05-26

### Added
- `BlueRetroDevice.async_set_output_config(port, device=..., accessory=...)` —
  set a port's device mode and/or accessory (2-byte write, no reboot).

## [0.3.1] - 2026-05-26

### Changed
- `async_read_vmu()` now raises a descriptive `RuntimeError` (including bytes
  read so far and the negotiated MTU) when the adapter rejects the chunked read,
  to diagnose VMU transfer failures on the BlueZ stack.

## [0.3.0] - 2026-05-26

### Added
- Read per-output config: `BlueRetroState.controller_mode` and `accessory`
  (device mode + accessory for output port 1), and
  `BlueRetroDevice.async_read_output_config(port)`.
- `BlueRetroDevice.async_read_vmu()` — download the emulated Dreamcast VMU
  (128 KiB), read-only.
- `DEVICE_CFG` and `ACCESSORY_CFG` enums.

## [0.2.0] - 2026-05-26

### Changed
- Restructured the project to a `src/` layout built with hatchling, with modules
  split into `const` / `protocol` / `scanner` / `device` / `models` / `gameid`
  (the `parser` module is now `protocol`, `discovery` is now `scanner`). The
  public API (`BlueRetroDevice`, `BlueRetroState`, `supports`, the enums) is
  unchanged.

### Added
- `scanner.discover()` to actively scan for nearby adapters, and a `blueretro`
  command-line tool (`blueretro scan|info|reboot|sleep`).
- ruff linting, a Python 3.11–3.13 CI matrix, Dependabot, and `HARDWARE.md`
  documenting the BLE protocol.

## [0.1.2] - 2026-05-25

### Added
- Read the global config: `system`, `multitap`, `inquiry_mode` and
  `memory_card_bank` (from `CHAR_GLOBAL_CFG`), plus the firmware name
  (`fw_name`). These reads are best-effort and won't break on older firmware.
- `BlueRetroDevice.async_factory_reset()` and `async_set_global_config()`
  (writes selected fields then reboots to apply).
- Exposed the `SYSTEM_CFG`, `MULTITAP_CFG` and `INQUIRY_MODE` enums.
- `scripts/validate_hardware.py` for reading a real adapter end-to-end.

## [0.1.1] - 2026-05-25

### Added
- `py.typed` marker so downstream projects pick up the library's type hints.
- GitHub Actions: test workflow on every push/PR and a tag-triggered PyPI release
  via trusted publishing (OIDC).
- Contributing guide, issue/PR templates, and README badges.

## [0.1.0] - 2026-05-25

### Added
- Initial release: protocol constants, byte parsers, advertisement discovery,
  `BlueRetroState` model, bundled-SQLite game name lookup, and `BlueRetroDevice`
  (read cycle + reboot/deep-sleep). Extracted from the Home Assistant integration.

[Unreleased]: https://github.com/hudsonbrendon/blueretro-ble/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.5.0
[0.4.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.4.0
[0.3.1]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.3.1
[0.3.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.3.0
[0.2.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.2.0
[0.1.2]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.2
[0.1.1]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.1
[0.1.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.0
