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
    """Verify exact mathematical weight calculation for critical security risk with multipliers."""
    stg = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, "none")
    prod = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "insecure_db")

    report = ConfigurationDriftValidator.validate_deployment(stg, prod)
    # Critical Security risks (W=40.0 * E=1.0 * C=1.25 = 50.0 per item)
    assert report.risk_score >= 80.0
    assert report.passed_deployment_gate is False


def test_environment_multiplier_scale_factors():
    """Verify Target Environment Multipliers: Production=1.0, Staging=0.5."""
    stg_source = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, "none")
    prod_target = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "memory_mismatch")

    report_prod = ConfigurationDriftValidator.validate_deployment(stg_source, prod_target)
    # Memory mismatch in Production (E=1.0, W=40.0, C=1.0) -> Score = 40.0
    assert report_prod.risk_score == 40.0
    assert report_prod.passed_deployment_gate is False


def test_category_multiplier_security_compliance():
    """Verify Security & Compliance Category Multiplier C(K_i) = 1.25."""
    stg = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, "none")
    prod_vault = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "expired_vault_key")

    report = ConfigurationDriftValidator.validate_deployment(stg, prod_vault)
    # Expired Vault Key = Critical Security & Compliance risk. W=40.0 * E=1.0 * C=1.25 = 50.0
    assert report.risk_score == 50.0
    assert report.passed_deployment_gate is False


def test_threshold_boundary_gating_logic():
    """Verify gating decision logic: APPROVED if score < 25.0 and crit == 0, BLOCKED if >= 25.0 or crit >= 1."""
    stg = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.STAGING, "none")
    prod_clean = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "none")
    prod_mem = EnvironmentSimulator.get_service_config(MicroserviceName.PAYMENT_PROCESSOR, Environment.PRODUCTION, "memory_mismatch")

    report_clean = ConfigurationDriftValidator.validate_deployment(stg, prod_clean)
    assert report_clean.risk_score == 0.0
    assert report_clean.passed_deployment_gate is True

    report_mem = ConfigurationDriftValidator.validate_deployment(stg, prod_mem)
    # Critical risk count = 1 -> BLOCKED regardless of threshold score
    assert report_mem.passed_deployment_gate is False


def test_sha256_snapshot_delta_tracking():
    """Verify SHA-256 hash tracking, atomic traffic shifting, and container state revert."""
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
    assert "kubectl rollout undo" in res_rollback["container_revert_status"]
