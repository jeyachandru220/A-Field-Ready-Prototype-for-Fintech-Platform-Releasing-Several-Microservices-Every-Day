"""
Pytest Test Suite for Pipeline Migration, Legacy Coexistence, and Automated Rollback.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from src.models import MicroserviceName, Environment
from pipeline.legacy_deploy import DeploymentPipeline, PipelineMode


def test_legacy_mode_deployment_allows_drift():
    """Verify legacy pipeline mode allows risky configuration drift into Production."""
    pipeline = DeploymentPipeline()

    res = pipeline.execute_deployment(
        service=MicroserviceName.PAYMENT_PROCESSOR,
        source_env=Environment.STAGING,
        target_env=Environment.PRODUCTION,
        mode=PipelineMode.LEGACY_UNSHIELDED,
        drift_scenario="insecure_db"
    )

    assert res["mode"] == "LEGACY_UNSHIELDED"
    assert res["status"] == "DEPLOYED_WITH_RISK"
    assert res["gate_passed"] is True


def test_shielded_mode_blocks_drift():
    """Verify shielded pipeline mode blocks risky configuration drift before Production."""
    pipeline = DeploymentPipeline()

    res = pipeline.execute_deployment(
        service=MicroserviceName.PAYMENT_PROCESSOR,
        source_env=Environment.STAGING,
        target_env=Environment.PRODUCTION,
        mode=PipelineMode.SHIELDED_VALIDATOR,
        drift_scenario="insecure_db"
    )

    assert res["mode"] == "SHIELDED_VALIDATOR"
    assert res["status"] == "BLOCKED_BY_DRIFT_VALIDATOR"
    assert res["gate_passed"] is False


def test_automated_rollback():
    """Verify automated rollback restores verified clean production snapshot."""
    pipeline = DeploymentPipeline()

    # Trigger rollback
    res = pipeline.trigger_rollback(MicroserviceName.PAYMENT_PROCESSOR)
    assert res["status"] == "ROLLBACK_SUCCESSFUL"
    assert "restored_snapshot_sha256" in res

    prod_cfg = pipeline.production_snapshots[MicroserviceName.PAYMENT_PROCESSOR.value]
    assert prod_cfg.env_vars.vars["PAYMENT_DB_SSLMODE"] == "require"
