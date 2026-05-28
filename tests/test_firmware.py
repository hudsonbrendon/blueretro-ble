from blueretro_ble.firmware import parse_firmware


def test_parse_firmware_full():
    assert parse_firmware("v24.04 hw1 playstation") == (
        "v24.04",
        "hw1",
        "Playstation",
    )


def test_parse_firmware_no_hw():
    assert parse_firmware("v1.8.1 gamecube") == ("v1.8.1", None, "Gamecube")


def test_parse_firmware_version_only():
    assert parse_firmware("v1.8.1") == ("v1.8.1", None, None)


def test_parse_firmware_empty():
    assert parse_firmware(None) == (None, None, None)
    assert parse_firmware("") == (None, None, None)


def test_parse_firmware_in_public_api():
    from blueretro_ble import parse_firmware as exported

    assert exported is parse_firmware
