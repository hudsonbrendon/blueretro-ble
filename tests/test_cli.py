import pytest

from blueretro_ble.__main__ import build_parser


def test_parser_scan():
    args = build_parser().parse_args(["scan"])
    assert args.command == "scan"


def test_parser_info_requires_address():
    args = build_parser().parse_args(["info", "AA:BB:CC:DD:EE:FF"])
    assert args.command == "info"
    assert args.address == "AA:BB:CC:DD:EE:FF"


def test_parser_reboot_and_sleep():
    assert build_parser().parse_args(["reboot", "X"]).command == "reboot"
    assert build_parser().parse_args(["sleep", "X"]).command == "sleep"


def test_parser_requires_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])
