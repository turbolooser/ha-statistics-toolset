"""Test configuration.

Put the integration directory on the path so the Home-Assistant-independent ``engine``
package can be imported directly, without triggering the HA-dependent package ``__init__``.
This is what makes the core mechanic unit-testable in isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path

_INTEGRATION = Path(__file__).resolve().parent.parent / "custom_components" / "statistics_toolset"
sys.path.insert(0, str(_INTEGRATION))
