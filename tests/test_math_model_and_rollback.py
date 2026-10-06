"""
Pytest Test Suite for Mathematical Risk Scoring Model and SHA-256 Automated Rollbacks.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.models import MicroserviceName, Environment, RiskLevel
from src.validator import ConfigurationDriftValidator
from simulation.environment_generator import EnvironmentSimulator
from pipeline.legacy_deploy import DeploymentPipeline, PipelineMode


def test_mathematical_risk_scoring_weights():
    """Verify exact mathematical weight calculation for critical and high risks."""
    stg = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, "none")
    prod = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "insecure_db")

    report = ConfigurationDriftValidator.validate_deployment(stg, prod)
    # Critical risk weight = 40.0. 2 critical drifts = 80.0
    assert report.risk_score >= 80.0
    assert report.passed_deployment_gate is False


def test_sha256_snapshot_delta_tracking():
    """Verify SHA-256 hash tracking and atomic traffic shifting rollback."""
    pipeline = DeploymentPipeline()

    # Initial hash
    init_hash = pipeline.snapshot_hashes[MicroserviceName.PAYMENT_PROCESSOR.value]
    assert len(init_hash) == 16

    # Execute legacy deployment with drift
    res_legacy = pipeline.execute_deployment(
        service=MicroserviceName.PAYMENT_PROCESSOR,
        source_env=Environment.STAGING,
        target_env=Environment.PRODUCTION,
        mode=PipelineMode.LEGACY_UNSHIELDED,
        drift_scenario="insecure_db"
    )
    assert res_legacy["snapshot_sha256"] != init_hash

    # Execute rollback
    res_rollback = pipeline.trigger_rollback(MicroserviceName.PAYMENT_PROCESSOR)
    assert res_rollback["status"] == "ROLLBACK_SUCCESSFUL"
    assert res_rollback["restored_snapshot_sha256"] == init_hash
    assert "Atomic ingress canary weight" in res_rollback["traffic_shift_status"]
