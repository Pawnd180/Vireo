"""Generate a 32x32 Vireo icon (dark tile with amber waveform bars)."""
import struct
from pathlib import Path

SIZE = 32
HEIGHTS = (8, 16, 24, 18, 10)
CENTERS = (6, 11, 16, 21, 26)


def pixel(x: int, y: int):
    red, green, blue = 18, 20, 26
    if x in (0, SIZE - 1) or y in (0, SIZE - 1):
        red, green, blue = 44, 48, 60
    for center, height in zip(CENTERS, HEIGHTS):
        if abs(x - center) <= 1 and 16 - height // 2 <= y <= 16 + height // 2:
            red, green, blue = 245, 158, 11
    return struct.pack("BBBB", blue, green, red, 255)


rows = []
for y in range(SIZE):
    rows.append(b"".join(pixel(x, y) for x in range(SIZE)))
pixels = b"".join(reversed(rows))
mask = b"\x00" * (SIZE * 4)
header = struct.pack("<IiiHHIIiiII", 40, SIZE, SIZE * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
image = header + pixels + mask
entry = struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(image), 22)
icon = struct.pack("<HHH", 0, 1, 1) + entry + image
target = Path(__file__).resolve().parent / "vireo.ico"
target.write_bytes(icon)
print("wrote %s (%d bytes)" % (target, len(icon)))
