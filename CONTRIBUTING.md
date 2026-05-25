# Contributing

Thanks for your interest in improving `blueretro-ble`!

## Development setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[test]"
pytest
```

Requires Python 3.12+.

## Guidelines

- The library is pure Python and must not depend on Home Assistant — it talks to the
  device over `bleak` only. HA-specific code belongs in the
  [integration repo](https://github.com/hudsonbrendon/blueretro-homeassistant).
- Add or update tests for any change; keep `pytest` green.
- Decoders in `parser.py` should stay pure (bytes in, value out) and never raise on
  malformed input — return `None` instead.
- The BLE protocol is reverse-engineered from `darthcloud/BlueRetroWebCfg`. When adding
  protocol coverage, cite the source and, where possible, verify against real hardware.

## Releasing

Releases publish to PyPI automatically via trusted publishing when a `v*` tag is pushed:

1. Bump `version` in `pyproject.toml` and update `CHANGELOG.md`.
2. Tag and push: `git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin vX.Y.Z`.
3. The `Release` workflow builds and publishes to PyPI.
