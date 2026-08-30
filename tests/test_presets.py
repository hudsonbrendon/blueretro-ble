from unittest.mock import AsyncMock, patch

import pytest

from blueretro_ble import (
    InputMapping,
    Preset,
    const,
    list_presets,
    load_preset,
    preset_from_json,
)
from blueretro_ble.buttons import BUTTONS
from blueretro_ble.device import BlueRetroDevice
from blueretro_ble.protocol import decode_input_config, encode_input_config


def test_bundled_presets_load_and_resolve():
    ids = list_presets()
    assert len(ids) >= 30
    assert "n64_fps" in ids
    for pid in ids:
        preset = load_preset(pid)
        assert preset.name and preset.console
        assert preset.mappings()  # every bundled preset yields >=1 mapping


def test_load_unknown_preset_raises():
    with pytest.raises(KeyError):
        load_preset("does_not_exist")


def test_mappings_resolve_names_and_offset_port():
    preset = preset_from_json(
        '{"name":"t","desc":"","console":"N64",'
        '"map":[["PAD_LX_LEFT","PAD_RX_LEFT",0,100,50,135,0,1,2]]}'
    )
    (m,) = preset.mappings(port=3)
    assert m == InputMapping(
        src=BUTTONS["PAD_LX_LEFT"], dest=BUTTONS["PAD_RX_LEFT"], dest_id=3,
        max=100, threshold=50, deadzone=135, turbo=0, scaling=1, diag_scaling=2,
    )
    # Round-trips through the wire encoding.
    assert decode_input_config(encode_input_config([m])) == [m]


def test_unknown_button_rows_are_skipped():
    preset = Preset(name="t", desc="", console="", map=[
        ["NOPE", "PAD_LX_LEFT", 0, 0, 0, 0, 0, 0, 0],
        ["PAD_LX_LEFT", "PAD_LX_LEFT", 0, 0, 0, 0, 0, 0, 0],
    ])
    assert len(preset.mappings()) == 1


async def test_apply_preset_writes_input_config():
    preset = preset_from_json(
        '{"name":"t","desc":"","console":"","map":[["PAD_LX_LEFT","PAD_LX_LEFT",0,100,50,135,0,0,0]]}'
    )
    client = AsyncMock()
    with patch(
        "blueretro_ble.device.establish_connection", AsyncMock(return_value=client)
    ):
        await BlueRetroDevice().async_apply_preset(AsyncMock(), preset, cfg_id=2, port=1)
    calls = client.write_gatt_char.await_args_list
    assert calls[0].args[0] == const.CHAR_IN_CFG_CTRL
    assert calls[1].args == (const.CHAR_IN_CFG_DATA, encode_input_config(preset.mappings(1)))
