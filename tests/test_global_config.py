from blueretro_ble.protocol import decode_global_config


def test_decode_full_payload():
    # system=PS2(17), multitap=Dual(3), inquiry=Manual(1), bank byte 2 -> bank 3
    assert decode_global_config(bytes([17, 3, 1, 2])) == ("PS2", "Dual", "Manual", 3)


def test_decode_defaults():
    assert decode_global_config(bytes([0, 0, 0, 0])) == ("Auto", "None", "Auto", 1)


def test_decode_short_payload_trailing_none():
    assert decode_global_config(bytes([6, 1])) == ("SNES", "Slot 1", None, None)


def test_decode_empty():
    assert decode_global_config(b"") == (None, None, None, None)


def test_decode_out_of_range_index_is_none():
    system, *_ = decode_global_config(bytes([200, 0, 0, 0]))
    assert system is None
