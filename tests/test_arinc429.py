import pytest

from app.arinc429 import build_word


def test_word_is_32_bits_and_odd_parity():
    word = build_word(label=0o203, sdi=2, value=12, resolution=1, ssm=0)
    assert 0 <= word < 2**32
    assert word.bit_count() % 2 == 1


def test_bnr_negative_value_sets_sign_bit():
    word = build_word(label=1, sdi=0, value=-5, resolution=1)
    assert word & (1 << 28)
    assert word.bit_count() % 2 == 1


def test_rejects_out_of_range_value():
    with pytest.raises(ValueError):
        build_word(label=1, sdi=0, value=2**18, resolution=1)
