"""
Pytest Test Suite for 4 Realistic Fintech Configuration Drift Edge & Failure Cases.
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


def test_clean_release_aligned():
    """Verify clean releases across Dev/Staging/Prod pass safety gate with 0 risk score."""
    for svc in MicroserviceName:
        stg_cfg = EnvironmentSimulator.get_service_config(svc, Environment.STAGING, "none")
        prd_cfg = EnvironmentSimulator.get_service_config(svc, Environment.PRODUCTION, "none")

        report = ConfigurationDriftValidator.validate_deployment(stg_cfg, prd_cfg)
        assert report.passed_deployment_gate is True
        assert report.risk_score == 0.0
        assert report.critical_count == 0


def test_failure_case_1_insecure_db_ssl():
    """Edge Case 1: Disabled SSL mode in Production DB connection string."""
    svc = MicroserviceName.PAYMENT_PROCESSOR
    stg_cfg = EnvironmentSimulator.get_service_config(svc, Environment.STAGING, "none")
    prd_cfg = EnvironmentSimulator.get_service_config(svc, Environment.PRODUCTION, "insecure_db")

    report = ConfigurationDriftValidator.validate_deployment(stg_cfg, prd_cfg)
    assert report.passed_deployment_gate is False
    assert report.critical_count >= 1
    assert any("sslmode" in d.key.lower() for d in report.drifts)
    assert any(d.risk_level == RiskLevel.CRITICAL for d in report.drifts)


def test_failure_case_2_vault_secret_expired():
    """Edge Case 2: Unrotated, expired Vault secret key in Production."""
    svc = MicroserviceName.AUTH_VAULT
    stg_cfg = EnvironmentSimulator.get_service_config(svc, Environment.STAGING, "none")
    prd_cfg = EnvironmentSimulator.get_service_config(svc, Environment.PRODUCTION, "expired_vault_key")

    report = ConfigurationDriftValidator.validate_deployment(stg_cfg, prd_cfg)
    assert report.passed_deployment_gate is False
    assert report.critical_count >= 1
    assert any("expired" in d.key.lower() for d in report.drifts)


def test_failure_case_3_memory_limit_mismatch():
    """Edge Case 3: IaC spec (4Gi) vs active container runtime limit (512MB) mismatch."""
    svc = MicroserviceName.LEDGER_CORE
    stg_cfg = EnvironmentSimulator.get_service_config(svc, Environment.STAGING, "none")
    prd_cfg = EnvironmentSimulator.get_service_config(svc, Environment.PRODUCTION, "memory_mismatch")

    report = ConfigurationDriftValidator.validate_deployment(stg_cfg, prd_cfg)
    assert report.passed_deployment_gate is False
    assert any("memory" in d.key.lower() for d in report.drifts)


def test_failure_case_4_missing_compliance_flag():
    """Edge Case 4: Missing/Disabled PCI-DSS compliance flag in Production."""
    svc = MicroserviceName.PAYMENT_PROCESSOR
    stg_cfg = EnvironmentSimulator.get_service_config(svc, Environment.STAGING, "none")
    prd_cfg = EnvironmentSimulator.get_service_config(svc, Environment.PRODUCTION, "missing_compliance_flag")

    report = ConfigurationDriftValidator.validate_deployment(stg_cfg, prd_cfg)
    assert report.passed_deployment_gate is False
    assert report.critical_count >= 1
    assert any("pan" in d.key.lower() for d in report.drifts)
