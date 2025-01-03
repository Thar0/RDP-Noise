#!/usr/bin/env python3
#
#   Converts a binary image of a 32-bit framebuffer full of noise pixels into bit samples.
#   The color combiner should be set to e.g. NOISE * PRIM_LOD_FRAC for PRIM_LOD_FRAC=255,
#   PRIM_LOD_FRAC may be substituted for any other constant input set to 255.
#
#   Usage: fb2data.py framebuffer.bin
#

import sys

with open(sys.argv[1], "rb") as infile:
    data = infile.read()

reduced_data = []
for i,b in enumerate(data):
    if i % 4 == 0:
        # read byte from red channel
        reduced_data.append(b)
    elif i % 4 == 3:
        # skip coverage
        continue
    else:
        # ensure grayscale
        assert b == reduced_data[-1], f"{b}, {reduced_data[-1]}"

A = []
B = []
C = []

# We're looking to decompose pixels that look like (bitwise) ABC100000 into separate datasets
# for the A,B,C bits. However, between these pixels and our observation of them the color combiner
# will have clamped them. We need to apply an inverse CC clamp:

for b in reduced_data:
    if b == 0xFF:
        # Saturated, looked like 10C100000 prior to CC clamp, sadly we can't recover C
        A.append(1)
        B.append(0)
        C.append(-1) # not recoverable
    elif b == 0x00:
        # Wrapped, looked like 11C100000 prior to CC clamp, sadly we can't recover C
        A.append(1)
        B.append(1)
        C.append(-1) # not recoverable
    else:
        # Account for CC multiplication bias
        if not ((b & 0b111111) == 0b100000):
            b += 1
        # By this point pixels that did not saturate or wrap should look like BC100000,
        # prior to clamp these would've been 0BC100000
        assert (b & 0b111111) == 0b100000, b

        A.append(0)
        B.append(b >> 7 & 1)
        C.append(b >> 6 & 1)

print(f"A_dataset = ", str(A).replace("[", "{").replace("]", "}"))
print(f"B_dataset = ", str(B).replace("[", "{").replace("]", "}"))
print(f"C_dataset = ", str(C).replace("[", "{").replace("]", "}"))
