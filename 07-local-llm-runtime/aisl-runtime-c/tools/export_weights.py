#!/usr/bin/env python3
"""Write one deterministic 2 x 3 FP32 matrix in AISL format version 1."""

import argparse
import struct
from pathlib import Path

MAGIC = b"AISL"
VERSION = 1
HEADER_SIZE = 32
DTYPE_F32 = 1
RANK = 2
ROWS = 2
COLS = 3
VALUES = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)


def export(path: Path) -> None:
    payload = struct.pack("<6f", *VALUES)
    header = struct.pack(
        "<4sHHIIIIQ",
        MAGIC,
        VERSION,
        HEADER_SIZE,
        DTYPE_F32,
        RANK,
        ROWS,
        COLS,
        len(payload),
    )
    assert len(header) == HEADER_SIZE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    export(args.output)
    print(f"wrote {args.output} ({HEADER_SIZE + len(VALUES) * 4} bytes)")


if __name__ == "__main__":
    main()
