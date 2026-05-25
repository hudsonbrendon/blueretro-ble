# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/hudsonbrendon/blueretro-ble/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hudsonbrendon/blueretro-ble/releases/tag/v0.1.0
