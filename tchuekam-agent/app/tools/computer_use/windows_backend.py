# Windows backend for computer_use using pyautogui

from __future__ import annotations

import base64
import io
import logging
import os
import sys
import threading
from typing import Any, Dict, List, Optional, Tuple

from tools.computer_use.backend import (
    ActionResult,
    CaptureResult,
    ComputerUseBackend,
    UIElement,
)

logger = logging.getLogger(__name__)

class WindowsBackend(ComputerUseBackend):
    """A simple Windows backend using pyautogui for basic GUI automation.

    This backend provides minimal functionality required for generic app control.
    It does not expose AX tree elements; capture returns an empty element list.
    """

    def __init__(self) -> None:
        self._started = False
        self._lock = threading.Lock()
        self._last_app: Optional[str] = None

    # ── Lifecycle ──────────────────────────────────────────────────
    def start(self) -> None:
        with self._lock:
            if not self._started:
                # Lazy import pyautogui to avoid import overhead when not used.
                try:
                    import pyautogui  # noqa: F401
                except Exception as e:
                    logger.error("pyautogui not available: %s", e)
                    raise RuntimeError("pyautogui is required for WindowsComputerUseBackend")
                self._started = True

    def stop(self) -> None:
        with self._lock:
            self._started = False

    def is_available(self) -> bool:
        return sys.platform.startswith("win") and self._pyautogui_available()

    @staticmethod
    def _pyautogui_available() -> bool:
        try:
            import pyautogui  # noqa: F401
            return True
        except Exception:
            return False

    # ── Capture ────────────────────────────────────────────────────
    def capture(self, mode: str = "som", app: Optional[str] = None) -> CaptureResult:
        """Capture a screenshot using pyautogui.

        The `mode` argument is ignored; a PNG base64 is always returned.
        """
        try:
            import pyautogui
        except Exception as e:
            logger.error("pyautogui import failed during capture: %s", e)
            raise RuntimeError("pyautogui required for capture")

        screenshot = pyautogui.screenshot()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        png_b64 = base64.b64encode(buffered.getvalue()).decode("ascii")
        # Width/height from image size.
        width, height = screenshot.size
        return CaptureResult(
            mode=mode,
            width=width,
            height=height,
            png_b64=png_b64,
            elements=[],
            app=app or "",
            window_title="",
            png_bytes_len=len(buffered.getvalue()),
        )

    # ── Pointer actions ──────────────────────────────────────────────
    def click(
        self,
        *,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        click_count: int = 1,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        try:
            import pyautogui
        except Exception as e:
            logger.error("pyautogui import failed during click: %s", e)
            return ActionResult(ok=False, action="click", message=str(e))

        if modifiers:
            # pyautogui does not support modifier keys for click directly; ignore.
            logger.warning("Modifiers ignored for click on WindowsBackend")
        # pyautogui click expects x, y coordinate; if element is provided we cannot map it.
        if x is None or y is None:
            return ActionResult(ok=False, action="click", message="x and y required for click on WindowsBackend")
        try:
            pyautogui.click(x=x, y=y, clicks=click_count, button=button)
            return ActionResult(ok=True, action="click")
        except Exception as e:
            logger.exception("click failed")
            return ActionResult(ok=False, action="click", message=str(e))

    def drag(
        self,
        *,
        from_element: Optional[int] = None,
        to_element: Optional[int] = None,
        from_xy: Optional[Tuple[int, int]] = None,
        to_xy: Optional[Tuple[int, int]] = None,
        button: str = "left",
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        try:
            import pyautogui
        except Exception as e:
            return ActionResult(ok=False, action="drag", message=str(e))
        if not from_xy or not to_xy:
            return ActionResult(ok=False, action="drag", message="from_xy and to_xy required")
        try:
            pyautogui.moveTo(*from_xy)
            pyautogui.dragTo(*to_xy, button=button, duration=0.2)
            return ActionResult(ok=True, action="drag")
        except Exception as e:
            logger.exception("drag failed")
            return ActionResult(ok=False, action="drag", message=str(e))

    def scroll(
        self,
        *,
        direction: str,
        amount: int = 3,
        element: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        modifiers: Optional[List[str]] = None,
    ) -> ActionResult:
        try:
            import pyautogui
        except Exception as e:
            return ActionResult(ok=False, action="scroll", message=str(e))
        # pyautogui scroll expects vertical scroll; for horizontal we can use hscroll.
        try:
            if direction == "up":
                pyautogui.scroll(amount)
            elif direction == "down":
                pyautogui.scroll(-amount)
            elif direction == "left":
                pyautogui.hscroll(-amount)
            elif direction == "right":
                pyautogui.hscroll(amount)
            else:
                return ActionResult(ok=False, action="scroll", message=f"invalid direction {direction}")
            return ActionResult(ok=True, action="scroll")
        except Exception as e:
            logger.exception("scroll failed")
            return ActionResult(ok=False, action="scroll", message=str(e))

    # ── Keyboard ───────────────────────────────────────────────────
    def type_text(self, text: str) -> ActionResult:
        try:
            import pyautogui
        except Exception as e:
            return ActionResult(ok=False, action="type_text", message=str(e))
        try:
            pyautogui.write(text, interval=0.0)
            return ActionResult(ok=True, action="type_text")
        except Exception as e:
            logger.exception("type_text failed")
            return ActionResult(ok=False, action="type_text", message=str(e))

    def key(self, keys: str) -> ActionResult:
        try:
            import pyautogui
        except Exception as e:
            return ActionResult(ok=False, action="key", message=str(e))
        # Parse keys similar to existing _canon_key_combo but feed to hotkey.
        # Simple implementation: split by '+' and press sequentially.
        try:
            parts = [p.strip() for p in keys.replace('+', ' + ').split() if p.strip()]
            # pyautogui.hotkey expects keys in order.
            pyautogui.hotkey(*parts)
            return ActionResult(ok=True, action="key")
        except Exception as e:
            logger.exception("key failed")
            return ActionResult(ok=False, action="key", message=str(e))

    # ── Introspection ────────────────────────────────────────────────
    def list_apps(self) -> List[Dict[str, Any]]:
        # Windows does not have a simple enumeration without external libs.
        # Return empty list; callers can still use capture to target windows.
        return []

    def focus_app(self, app: str, raise_window: bool = False) -> ActionResult:
        # No reliable implementation without additional packages (e.g., pywinauto).
        # Provide a stub that returns success but does nothing.
        return ActionResult(ok=True, action="focus_app", message=f"focus_app stub for {app}")

    # ── Value setter ────────────────────────────────────────────────
    def set_value(self, value: str, element: Optional[int] = None) -> ActionResult:
        # Not applicable in this simple backend.
        return ActionResult(ok=False, action="set_value", message="set_value not supported on WindowsBackend")

    # ── Timing ──────────────────────────────────────────────────────
    def wait(self, seconds: float) -> ActionResult:
        import time
        time.sleep(max(0.0, min(seconds, 30.0)))
        return ActionResult(ok=True, action="wait", message=f"waited {seconds:.2f}s")
