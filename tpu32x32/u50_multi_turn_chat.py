#!/usr/bin/env python3
"""Multi-turn entry point for the packaged Alveo U50 binary runtime."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True
from u50_chat import tpu32x32_runtime_core


if __name__ == "__main__":
    try:
        raise SystemExit(tpu32x32_runtime_core.main([
            "--interactive", *sys.argv[1:],
        ]))
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
