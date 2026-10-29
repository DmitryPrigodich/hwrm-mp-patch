"""Render the original geometric three-person SU glyph; no donor image is edited."""

import math
import struct

SIZE = 128
REAR = [
    (38, 28, 12, [(25, 45), (51, 45), (62, 56), (62, 82), (14, 82), (14, 56)]),
    (90, 28, 12, [(77, 45), (103, 45), (114, 56), (114, 82), (66, 82), (66, 56)]),
]
FRONT = (64, 45, 15, [(47, 65), (81, 65), (97, 79), (97, 111), (31, 111), (31, 79)])


def polygon(x, y, points):
    inside = False
    distance = 1e9
    for i, (ax, ay) in enumerate(points):
        bx, by = points[(i + 1) % len(points)]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            inside = not inside
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        distance = min(distance, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return -distance if inside else distance


def color(x, y):
    result = None
    for cx, cy, radius, body in REAR + [FRONT]:
        neck = [
            (cx - 5, cy + radius - 3),
            (cx + 5, cy + radius - 3),
            (cx + 5, body[0][1] + 2),
            (cx - 5, body[0][1] + 2),
        ]
        distance = min(
            math.hypot(x - cx, y - cy) - radius, polygon(x, y, body), polygon(x, y, neck)
        )
        if distance <= 2:
            result = (250, 133, 43)
        if distance <= 0:
            t = max(0, min(1, (y - 16) / 95))
            result = (255, round(229 - 37 * t), round(132 - 52 * t))
        if -1.1 <= distance <= 0 and y < 80:
            result = (255, 235, 153)
    return result


def generate(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pixels = bytearray()
    for y in reversed(range(SIZE)):
        for x in range(SIZE):
            samples = [color(x + dx, y + dy) for dx in (0.25, 0.75) for dy in (0.25, 0.75)]
            covered = [c for c in samples if c is not None]
            rgb = (
                [round(sum(c[i] for c in covered) / len(covered)) for i in range(3)]
                if covered
                else [0, 0, 0]
            )
            pixels.extend([rgb[2], rgb[1], rgb[0], round(255 * len(covered) / 4)])
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 8)
    path.write_bytes(header + pixels)
