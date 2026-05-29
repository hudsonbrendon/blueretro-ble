import random

from blueretro_ble import PAK_SIZE, make_formatted_pak


def test_formatted_pak_size():
    assert len(make_formatted_pak()) == PAK_SIZE


def test_formatted_pak_checksum_valid():
    data = make_formatted_pak(random.Random(42))
    block = data[32:64]
    sum_a = 0
    for i in range(0, 28, 2):
        sum_a = (sum_a + ((block[i] << 8) + block[i + 1])) & 0xFFFF
    stored_a = (block[28] << 8) | block[29]
    stored_b = (block[30] << 8) | block[31]
    assert stored_a == sum_a
    # The two checksums sum to the magic 0xFFF2 (mod 16 bits).
    assert (stored_a + stored_b) & 0xFFFF == 0xFFF2


def test_formatted_pak_header_mirrored():
    data = make_formatted_pak(random.Random(7))
    page = data[32:64]
    assert data[96:128] == page
    assert data[128:160] == page
    assert data[192:224] == page


def test_formatted_pak_reproducible_with_seed():
    assert make_formatted_pak(random.Random(1)) == make_formatted_pak(
        random.Random(1)
    )
