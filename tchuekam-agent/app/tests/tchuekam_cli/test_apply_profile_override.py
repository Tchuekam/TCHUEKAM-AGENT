"""Regression tests for _apply_profile_override TCHUEKAM_HOME guard (issue #22502).

When TCHUEKAM_HOME is set to the tchuekam root (e.g. systemd hardcodes
TCHUEKAM_HOME=/root/.tchuekam), _apply_profile_override must still read
active_profile and update TCHUEKAM_HOME to the profile directory.

When TCHUEKAM_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, tchuekam_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["TCHUEKAM_HOME"] after the call,
    or None if unset.
    """
    tchuekam_root = tmp_path / ".tchuekam"
    tchuekam_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (tchuekam_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (tchuekam_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if tchuekam_home is not None:
        monkeypatch.setenv("TCHUEKAM_HOME", tchuekam_home)
    else:
        monkeypatch.delenv("TCHUEKAM_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["tchuekam", "gateway", "start"])

    from tchuekam_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("TCHUEKAM_HOME")


class TestApplyProfileOverrideTchuEkaMHomeGuard:
    """Regression guard for issue #22502.

    Verifies that TCHUEKAM_HOME pointing to the tchuekam root does NOT suppress
    the active_profile check, while TCHUEKAM_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_tchuekam_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """TCHUEKAM_HOME=/root/.tchuekam + active_profile=coder must redirect
        TCHUEKAM_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets TCHUEKAM_HOME to the tchuekam root
        and the user switches to a profile via `tchuekam profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        tchuekam_root = tmp_path / ".tchuekam"
        tchuekam_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            tchuekam_home=str(tchuekam_root),
            active_profile="coder",
        )

        assert result is not None, "TCHUEKAM_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected TCHUEKAM_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected TCHUEKAM_HOME to end with 'coder', got: {result!r}"
        )

    def test_tchuekam_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """TCHUEKAM_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with TCHUEKAM_HOME already set to a specific profile must stay in that
        profile.
        """
        tchuekam_root = tmp_path / ".tchuekam"
        profile_dir = tchuekam_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (tchuekam_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("TCHUEKAM_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["tchuekam", "gateway", "start"])

        from tchuekam_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("TCHUEKAM_HOME") == str(profile_dir), (
            "TCHUEKAM_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_tchuekam_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: TCHUEKAM_HOME unset + active_profile=coder must set
        TCHUEKAM_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            tchuekam_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_tchuekam_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect TCHUEKAM_HOME."""
        tchuekam_root = tmp_path / ".tchuekam"
        tchuekam_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("TCHUEKAM_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["tchuekam", "gateway", "start"])
        (tchuekam_root / "active_profile").write_text("default")

        from tchuekam_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("TCHUEKAM_HOME") is None
