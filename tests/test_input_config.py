import pytest

from blueretro_ble import InputMapping, decode_input_config, encode_input_config


def test_encode_header_and_size():
    blob = encode_input_config([InputMapping(src=1, dest=2)])
    assert blob[:3] == bytes([0, 0, 1])
    assert len(blob) == 1 * 8 + 3


def test_scaling_nibbles_packed():
    blob = encode_input_config(
        [InputMapping(src=0, dest=0, scaling=0x3, diag_scaling=0x2)]
    )
    assert blob[3 + 7] == (0x3 | (0x2 << 4))


def test_roundtrip():
    maps = [
        InputMapping(
            src=1, dest=2, dest_id=3, max=255, threshold=50,
            deadzone=10, turbo=4, scaling=1, diag_scaling=2,
        ),
        InputMapping(src=5, dest=6),
    ]
    assert decode_input_config(encode_input_config(maps)) == maps


def test_decode_empty():
    assert decode_input_config(b"") == []
    assert decode_input_config(bytes([0, 0, 0])) == []


def test_encode_rejects_out_of_range():
    with pytest.raises(ValueError):
        encode_input_config([InputMapping(src=999, dest=0)])


def test_encode_rejects_too_many():
    with pytest.raises(ValueError):
        encode_input_config([InputMapping(src=0, dest=0)] * 256)
