"""Unit tests for the stepped light ramp math.

Loads the pure helpers via the ``pure`` fixture (defined in
tests/conftest.py) so the full integration package — and its HA imports —
never get touched.
"""
from __future__ import annotations

from types import ModuleType

import pytest


class TestComputeStepTarget:
    def test_first_step_starts_at_one_percent(self, pure: ModuleType) -> None:
        pct, _ = pure.compute_step_target(
            0, total_steps=300, max_pct=35, start_k=1500, target_k=4500
        )
        assert pct == 1

    def test_first_step_starts_at_start_kelvin(self, pure: ModuleType) -> None:
        _, k = pure.compute_step_target(
            0, total_steps=300, max_pct=35, start_k=1500, target_k=4500
        )
        assert k == 1500

    def test_last_step_reaches_max_pct(self, pure: ModuleType) -> None:
        pct, _ = pure.compute_step_target(
            299, total_steps=300, max_pct=35, start_k=1500, target_k=4500
        )
        assert pct == 35

    def test_last_step_reaches_target_kelvin(self, pure: ModuleType) -> None:
        _, k = pure.compute_step_target(
            299, total_steps=300, max_pct=35, start_k=1500, target_k=4500
        )
        assert k == 4500

    def test_midpoint_is_halfway_in_kelvin(self, pure: ModuleType) -> None:
        # idx == (total_steps - 1) / 2 with total_steps == 11 → idx == 5
        _, k = pure.compute_step_target(
            5, total_steps=11, max_pct=100, start_k=2000, target_k=4000
        )
        assert k == 3000

    def test_total_steps_one_returns_max_immediately(self, pure: ModuleType) -> None:
        pct, k = pure.compute_step_target(
            0, total_steps=1, max_pct=35, start_k=1500, target_k=4500
        )
        assert pct == 35
        assert k == 4500

    def test_brightness_monotonic(self, pure: ModuleType) -> None:
        prev = -1
        for idx in range(20):
            pct, _ = pure.compute_step_target(
                idx, total_steps=20, max_pct=80, start_k=2000, target_k=4000
            )
            assert pct >= prev
            prev = pct

    def test_kelvin_monotonic(self, pure: ModuleType) -> None:
        prev = -1
        for idx in range(20):
            _, k = pure.compute_step_target(
                idx, total_steps=20, max_pct=80, start_k=2000, target_k=4000
            )
            assert k >= prev
            prev = k

    def test_kelvin_can_decrease_when_target_lower_than_start(
        self, pure: ModuleType
    ) -> None:
        # User picks a warmer target than start (unusual but valid)
        _, k0 = pure.compute_step_target(
            0, total_steps=10, max_pct=50, start_k=4000, target_k=2000
        )
        _, k9 = pure.compute_step_target(
            9, total_steps=10, max_pct=50, start_k=4000, target_k=2000
        )
        assert k0 == 4000
        assert k9 == 2000


class TestClampKelvin:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (1000, 1500),
            (1500, 1500),
            (3000, 3000),
            (6500, 6500),
            (7000, 6500),
            (-100, 1500),
        ],
    )
    def test_clamps_to_1500_6500(
        self, pure: ModuleType, raw: int, expected: int
    ) -> None:
        assert pure.clamp_kelvin(raw) == expected
