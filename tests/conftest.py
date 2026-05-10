"""Test bootstrap: load the integration's pure-helper module in isolation.

The full ``custom_components.wake_alarm`` package imports a long tail of
``homeassistant`` modules in its __init__.py and submodules, none of which
are available outside a real Home Assistant runtime. We side-step that by
loading ``custom_components/wake_alarm/_pure.py`` directly via
``importlib.util.spec_from_file_location`` — that module deliberately has
zero HA imports, so unit tests can pull pure helpers out of it without
provisioning a hass fixture.

Tests that want full integration coverage should later layer
``pytest-homeassistant-custom-component`` on top.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent
PURE_PATH = ROOT / "custom_components" / "wake_alarm" / "_pure.py"


def _load_pure() -> ModuleType:
    spec = importlib.util.spec_from_file_location("wake_alarm_pure", PURE_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover
        raise RuntimeError(f"could not load {PURE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["wake_alarm_pure"] = module
    spec.loader.exec_module(module)
    return module


_PURE = _load_pure()


@pytest.fixture(scope="session")
def pure() -> ModuleType:
    """The wake_alarm pure-helpers module, loaded outside the package."""
    return _PURE
