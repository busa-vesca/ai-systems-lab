# AISL Runtime C — Phase 1

This phase defines and validates a tiny versioned binary weight format. It loads
one non-square, row-major FP32 matrix with ordinary file I/O. It does not use
`mmap`, run inference, or implement Transformer operations.

## Data flow

```text
known Python values -> exporter -> .bin file -> C validator -> owned float buffer
```

## Version 1 file layout

All multi-byte fields and FP32 values are little-endian. The header is decoded
field by field; it is never cast directly to a C struct.

| Offset | Bytes | Field | Required value |
|---:|---:|---|---|
| 0 | 4 | magic | ASCII `AISL` |
| 4 | 2 | version | `1` |
| 6 | 2 | header size | `32` |
| 8 | 4 | data type | `1` (FP32) |
| 12 | 4 | rank | `2` |
| 16 | 4 | rows | greater than zero |
| 20 | 4 | columns | greater than zero |
| 24 | 8 | payload bytes | `rows * columns * 4` |
| 32 | variable | payload | row-major FP32 values |

The complete file size must be exactly `32 + payload bytes`. Both missing and
extra bytes are rejected.

## Ownership and lifetime

On success, `aisl_weights_load` allocates `weights.data` and transfers ownership
to its caller. The caller must eventually call `aisl_weights_free`. The cleanup
function accepts a zero-initialized or already-freed value and resets every
field. On failure, the reader releases any partial allocation and leaves the
output empty.

This ownership model is intentionally temporary. Phase 2 will introduce a
separate non-owning view into an `mmap` region.

## Build and verify

```sh
make
make test
make sanitize
```

The normal build uses C11 with `-Wall -Wextra -Wpedantic`. The sanitizer target
is separate because sanitizer availability depends on the compiler and system.

To export and inspect the deterministic 2 x 3 matrix manually:

```sh
python3 tools/export_weights.py build/weights.bin
build/inspect_weights build/weights.bin
```

The reader tests cover a valid file, truncated header and payload, bad magic,
version, header size, data type and rank, zero dimensions, arithmetic overflow,
an inconsistent payload size, and trailing bytes.
