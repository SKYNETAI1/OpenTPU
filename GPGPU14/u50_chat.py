#!/usr/bin/env python3
"""Launch the packaged GPUTensor14 Alveo U50 runtime."""

from __future__ import annotations

import os
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = PACKAGE_ROOT / "runtime"
os.environ.setdefault("GPUTENSOR14_RUNTIME_ROOT", str(PACKAGE_ROOT))
sys.path.insert(0, str(RUNTIME_DIR))

from gputensor14_runtime_core import main


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
