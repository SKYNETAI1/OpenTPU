#!/usr/bin/env python3
"""Launch GPUTensor16 in interactive multi-turn mode."""

from __future__ import annotations

import os
from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = PACKAGE_ROOT / "runtime"
os.environ.setdefault("GPUTENSOR16_RUNTIME_ROOT", str(PACKAGE_ROOT))
sys.path.insert(0, str(RUNTIME_DIR))

from gputensor16_runtime_core import main


if __name__ == "__main__":
    raise SystemExit(main(["--interactive", *sys.argv[1:]]))
