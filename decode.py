"""
picoCTF 2021 - "Transformation" (Reverse Engineering, Easy)
Decoder script

The original challenge scrambled the flag using this logic:

    enc = "".join(
        [chr((ord(flag[i]) << 8) + ord(flag[i + 1])) for i in range(0, len(flag), 2)]
    )

In plain terms: it grabbed the flag two characters at a time, turned each
character into its numeric code, shifted the first one's code 8 bits to the
left (multiplying it by 256), added the second character's code on top of it,
and converted that combined number back into a single new character.

The result is that every PAIR of original 8-bit characters becomes ONE new
16-bit character in the output file ("enc").

To decode it, we do the reverse: take each scrambled character, split its
number back into two original bytes, and rebuild the string. Since we don't
know upfront whether the original packing was big-endian or little-endian,
this script tries both and prints each result so you can see which one comes
out as clean, readable text.

Usage:
    python3 decode.py
    (expects a file named "enc" in the same directory)
"""

from pathlib import Path

# Read the scrambled/encoded file as UTF-8 text.
# This is the file we downloaded from the challenge, containing the
# "squashed together" 16-bit characters.
s = Path("enc").read_text(encoding="utf-8")

# Try both possible byte orders, since we don't know which one the
# original encoding script effectively used.
for endian in ("big", "little"):
    # For every character in the scrambled text:
    #   1. ord(c)            -> turn the character back into its number
    #   2. .to_bytes(2, ...)  -> split that number into its 2 original bytes,
    #                            in either big-endian or little-endian order
    #   3. b"".join(...)     -> glue all the byte pairs back together
    raw = b"".join(ord(c).to_bytes(2, endian) for c in s)

    # Print which ordering we tried, next to the resulting bytes, so we can
    # visually compare and spot the real, readable flag.
    print(endian, repr(raw))

# Expected output:
#   big    b'picoCTF{16_bits_inst34d_of_8_b7f62ca5}'   <-- this is the flag
#   little b'ipocTC{F61b_ti_snits43_dfo8_b_f726ac}5'   <-- wrong byte order, garbled
