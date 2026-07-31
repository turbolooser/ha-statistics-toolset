"""Static check for undefined names (missing imports).

conftest.py deliberately avoids importing the integration's ``__init__.py`` (it depends on
Home Assistant, which is not installed here), and the backup/restore stub loads
``recorder_io``/``coordinator`` directly without going through it either. That gap once let
a missing import — ``WRITE_ALLOWLIST`` used in ``__init__.py`` but never imported — reach a
real Home Assistant instance and fail at startup, instead of failing here.

pyflakes catches this without needing Home Assistant: it resolves names statically, so a
name used but never bound anywhere in the module is flagged regardless of whether the branch
that uses it ever ran in a test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_INTEGRATION = Path(__file__).resolve().parent.parent / "custom_components" / "statistics_toolset"


def test_no_undefined_names_in_the_integration() -> None:
    files = sorted(_INTEGRATION.glob("*.py")) + sorted(_INTEGRATION.glob("engine/*.py"))
    result = subprocess.run(
        [sys.executable, "-m", "pyflakes", *[str(f) for f in files]],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"pyflakes found issues:\n{result.stdout}{result.stderr}"


def test_clear_statistic_uses_the_recorder_thread_safe_api() -> None:
    """Regression guard for "Detected unsafe call not in recorder thread" on restore.

    ``clear_statistics`` (the raw function) asserts it runs on the recorder's own worker
    thread. ``instance.async_add_executor_job`` runs on a *different* thread — the
    recorder's generic db-executor pool — so calling it that way raises exactly that error,
    but only against a real Home Assistant instance; nothing in the stubbed test suite runs
    on real threads, so this regression class doesn't fail there. The correct path is
    ``instance.async_clear_statistics(ids, on_done=...)``, queued onto the recorder thread,
    with its callback bridged back via ``hass.loop.call_soon_threadsafe`` — the same pattern
    the recorder's own ``recorder/clear_statistics`` websocket handler uses.
    """
    source = (_INTEGRATION / "recorder_io.py").read_text(encoding="utf-8")
    assert "async_clear_statistics" in source
    assert "call_soon_threadsafe" in source
    assert "from homeassistant.components.recorder.statistics import (" in source
    # The raw function must not be imported at all — importing it back is how this would
    # regress: nothing stops someone from also calling it directly again.
    import_block = source.split("from homeassistant.components.recorder.statistics import (")[
        1
    ].split(")")[0]
    assert "clear_statistics" not in import_block, (
        "the raw clear_statistics function must not be imported — use "
        "instance.async_clear_statistics via clear_statistic() instead"
    )
