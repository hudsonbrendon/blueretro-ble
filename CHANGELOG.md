# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/hudsonbrendon/blueretro-ble/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.2.0
[0.1.2]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.2
[0.1.1]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.1
[0.1.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.0
