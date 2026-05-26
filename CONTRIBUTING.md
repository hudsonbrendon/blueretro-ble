# Contributing

Thanks for your interest in improving `blueretro-ble`!

## Development setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
```

Requires Python 3.11+.

## Layout

```
src/blueretro_ble/
  const.py      # UUIDs, command bytes, config enums
  protocol.py   # pure byte decoders (bytes in, value out)
  scanner.py    # supports() predicate + discover()
  device.py     # BlueRetroDevice (connect -> read/write -> disconnect)
  models.py     # BlueRetroState
  gameid.py     # SQLite game-name lookup
  __main__.py   # `blueretro` CLI
```

## Guidelines

- The library is pure Python and must not depend on Home Assistant — it talks to the
  device over `bleak` only. HA-specific code belongs in the
  [integration repo](https://github.com/hudsonbrendon/blueretro-homeassistant).
- Add or update tests for any change; keep `pytest` and `ruff check .` green.
- Decoders in `protocol.py` should stay pure (bytes in, value out) and never raise on
  malformed input — return `None` instead.
- The BLE protocol is reverse-engineered from `darthcloud/BlueRetroWebCfg` (see
  `HARDWARE.md`). When adding protocol coverage, cite the source and, where possible,
  verify against real hardware.

## Releasing

Publishing to PyPI happens via trusted publishing (OIDC) when a GitHub release is
published:

1. Bump `version` in `pyproject.toml` and update `CHANGELOG.md`.
2. Tag and push: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`.
3. Create a GitHub release for the tag — the `Publish` workflow builds and uploads to PyPI.
