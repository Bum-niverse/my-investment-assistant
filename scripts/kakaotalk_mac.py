#!/usr/bin/env python3
"""Project-local wrapper for the kakaotalk-mac skill helper."""

from pathlib import Path
import runpy


HELPER = Path.home() / ".agents" / "skills" / "kakaotalk-mac" / "scripts" / "kakaotalk_mac.py"

if not HELPER.exists():
    raise SystemExit(f"kakaotalk-mac helper not found: {HELPER}")

runpy.run_path(str(HELPER), run_name="__main__")
