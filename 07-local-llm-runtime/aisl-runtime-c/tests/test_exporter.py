#!/usr/bin/env python3
"""Independent byte-level checks for the deterministic exporter output."""

import struct
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> None:
    project = Path(__file__).resolve().parents[1]
    exporter = project / "tools" / "export_weights.py"

    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "weights.bin"
        subprocess.run([sys.executable, str(exporter), str(output)], check=True)
        raw = output.read_bytes()

    assert len(raw) == 56
    assert raw[:4] == b"AISL"
    fields = struct.unpack("<4sHHIIIIQ", raw[:32])
    assert fields == (b"AISL", 1, 32, 1, 2, 2, 3, 24)
    assert struct.unpack("<6f", raw[32:]) == (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
    print("exporter test: PASS")


if __name__ == "__main__":
    main()
