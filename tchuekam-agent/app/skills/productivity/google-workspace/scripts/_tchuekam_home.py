"""Resolve TCHUEKAM_HOME for standalone skill scripts.

Skill scripts may run outside the TchuEkaM process (e.g. system Python,
nix env, CI) where ``tchuekam_constants`` is not importable.  This module
provides the same ``get_tchuekam_home()`` and ``display_tchuekam_home()``
contracts as ``tchuekam_constants`` without requiring it on ``sys.path``.

When ``tchuekam_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``tchuekam_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``TCHUEKAM_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from tchuekam_constants import display_tchuekam_home as display_tchuekam_home
    from tchuekam_constants import get_tchuekam_home as get_tchuekam_home
except (ModuleNotFoundError, ImportError):

    def get_tchuekam_home() -> Path:
        """Return the TchuEkaM home directory (default: ~/.tchuekam).

        Mirrors ``tchuekam_constants.get_tchuekam_home()``."""
        val = os.environ.get("TCHUEKAM_HOME", "").strip()
        return Path(val) if val else Path.home() / ".tchuekam"

    def display_tchuekam_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``tchuekam_constants.display_tchuekam_home()``."""
        home = get_tchuekam_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
