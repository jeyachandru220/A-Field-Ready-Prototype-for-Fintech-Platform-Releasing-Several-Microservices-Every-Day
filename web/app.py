"""
FastAPI Application Web Server for Fintech Microservice Configuration-Drift Dashboard.
Serves REST APIs for live validation, pipeline simulation, rollbacks, and benchmark experiments.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.models import MicroserviceName, Environment
from src.validator import ConfigurationDriftValidator
from simulation.environment_generator import EnvironmentSimulator
from pipeline.legacy_deploy import DeploymentPipeline, PipelineMode
from experiments.benchmark import DeploymentBenchmarkExperiment


app = FastAPI(
    title="Fintech Microservice Configuration-Drift Validator API",
    description="Multi-layered drift inspection, legacy migration pipeline, and automated rollbacks.",
    version="2.4.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance for in-memory simulation tracking
pipeline_orchestrator = DeploymentPipeline()


class ValidateRequest(BaseModel):
    service: MicroserviceName
    source_env: Environment = Environment.STAGING
    target_env: Environment = Environment.PRODUCTION
    drift_scenario: str = "none"


class DeployRequest(BaseModel):
    service: MicroserviceName
    source_env: Environment = Environment.STAGING
    target_env: Environment = Environment.PRODUCTION
    mode: PipelineMode = PipelineMode.SHIELDED_VALIDATOR
    drift_scenario: str = "none"


class RollbackRequest(BaseModel):
    service: MicroserviceName


@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY", "version": "2.4.0", "service": "Fintech Drift Validator API"}


@app.get("/api/options")
def get_options():
    return {
        "services": [s.value for s in MicroserviceName],
        "environments": [e.value for e in Environment],
        "scenarios": [
            {"id": "none", "name": "Clean Release (No Drift)", "description": "Perfectly aligned staging to production release"},
            {"id": "insecure_db", "name": "Edge Case 1: Insecure DB SSL Mode (sslmode=disable)", "description": "Disabled TLS in production database connection string"},
            {"id": "expired_vault_key", "name": "Edge Case 2: Vault Secret Key Rotation Expired", "description": "Production uses unrotated expired vault key v1 while Staging has v2"},
            {"id": "memory_mismatch", "name": "Edge Case 3: IaC Spec vs Container Memory Limit Mismatch", "description": "IaC requests 4Gi memory limit, but active container is capped at 512MB"},
            {"id": "missing_compliance_flag", "name": "Edge Case 4: Missing PCI-DSS Compliance Flag", "description": "MANDATE_STRIP_PAN is set to false in Production"},
            {"id": "sandbox_url_leak", "name": "Edge Case 5: Staging Bank Endpoint URL Leaked to Prod", "description": "Staging sandbox bank URL leaked into Production env vars"}
        ]
    }


@app.post("/api/validate")
def validate_configuration(req: ValidateRequest):
    src_cfg = EnvironmentSimulator.get_service_config(req.service, req.source_env, "none")
    tgt_cfg = EnvironmentSimulator.get_service_config(req.service, req.target_env, req.drift_scenario)

    report = ConfigurationDriftValidator.validate_deployment(src_cfg, tgt_cfg)

    # Include raw configs for side-by-side comparison UI
    return {
        "report": report.model_dump(),
        "source_config": src_cfg.model_dump(),
        "target_config": tgt_cfg.model_dump()
    }


@app.post("/api/deploy")
def simulate_deployment(req: DeployRequest):
    res = pipeline_orchestrator.execute_deployment(
        service=req.service,
        source_env=req.source_env,
        target_env=req.target_env,
        mode=req.mode,
        drift_scenario=req.drift_scenario
    )
    return res


@app.post("/api/rollback")
def execute_rollback(req: RollbackRequest):
    res = pipeline_orchestrator.trigger_rollback(req.service)
    return res


@app.get("/api/pipeline-history")
def get_pipeline_history():
    return {
        "history": pipeline_orchestrator.deployment_history,
        "active_production_snapshots": {
            svc: cfg.model_dump() for svc, cfg in pipeline_orchestrator.production_snapshots.items()
        }
    }


@app.get("/api/benchmark")
def run_benchmark_experiment(scenarios: int = Query(default=50, ge=10, le=100)):
    results = DeploymentBenchmarkExperiment.run_benchmark(scenarios)
    return results


# Mount static directory for Web UI
static_path = Path(__file__).resolve().parent / "static"
if static_path.exists():
    app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")
