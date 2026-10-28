"""ARINC 429 word builder for lab/test use; not a certified transmitter."""


def _odd_parity_bit(bits_1_to_31: int) -> int:
    return 0 if bits_1_to_31.bit_count() % 2 else 1


def build_word(*, label: int, sdi: int, value: float, resolution: float, ssm: int = 0) -> int:
    """Build a 32-bit BNR word. Label is stored in ARINC wire bit order (reversed)."""
    if not 0 <= label <= 255 or not 0 <= sdi <= 3 or not 0 <= ssm <= 3:
        raise ValueError("label, SDI o SSM fuera de rango")
    if resolution <= 0:
        raise ValueError("resolution debe ser mayor que cero")
    scaled = round(value / resolution)
    if not -(1 << 18) < scaled < (1 << 18):
        raise ValueError("valor excede el rango BNR de 18 bits más signo")

    # Bits 1-8 label (LSB first on wire), 9-10 SDI, 11-28 magnitude,
    # 29 sign, 30-31 SSM, 32 odd parity.
    wire_label = int(f"{label:08b}"[::-1], 2)
    data = abs(scaled) & 0x3FFFF
    word = wire_label | (sdi << 8) | (data << 10) | (ssm << 29)
    if scaled < 0:
        word |= 1 << 28
    word |= _odd_parity_bit(word) << 31
    return word
