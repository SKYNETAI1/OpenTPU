#!/usr/bin/env python3
"""Public launcher for the packaged Alveo U50 binary runtime."""

from __future__ import annotations

import os
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
RUNTIME_DIR = HERE / "runtime"
os.environ.setdefault("TPU32X32_RUNTIME_ROOT", str(HERE))
sys.path.insert(0, str(RUNTIME_DIR))

try:
    import tpu32x32_runtime_core
except ImportError as error:
    raise SystemExit(
        "Unable to load the packaged U50 runtime. This release requires "
        "64-bit CPython 3.12 on Linux.\n"
        f"Runtime directory: {RUNTIME_DIR}\n"
        f"Original error: {error}"
    ) from error


if __name__ == "__main__":
    try:
        raise SystemExit(tpu32x32_runtime_core.main())
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise
