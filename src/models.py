"""
Data models for Fintech Microservices Configuration-Drift Validator.
Defines schemas for 4 configuration layers, drift findings, risk levels, and validation reports.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class MicroserviceName(str, Enum):
    PAYMENT_PROCESSOR = "payment-processor"
    LEDGER_CORE = "ledger-core"
    AUTH_VAULT = "auth-vault"
    RISK_ENGINE = "risk-engine"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"  # Immediate security/financial risk (e.g. unencrypted prod secrets, disabled TLS)
    HIGH = "HIGH"          # High reliability/outage risk (e.g. IaC vs runtime memory mismatch, low DB pool)
    MEDIUM = "MEDIUM"      # Moderate operational risk (e.g. unrotated vault key close to expiry)
    LOW = "LOW"            # Non-blocking minor drift (e.g. verbose logging level in staging)
    INFO = "INFO"          # Expected env-specific difference (e.g. replica count dev=1 vs prod=5)


# Layer 1: Infrastructure Definitions (IaC / K8s / Compose)
class InfrastructureSpec(BaseModel):
    cpu_request: str = "500m"
    cpu_limit: str = "1000m"
    memory_request: str = "1Gi"
    memory_limit: str = "2Gi"
    min_replicas: int = 2
    max_replicas: int = 10
    container_port: int = 8080
    ingress_tls_enabled: bool = True
    readiness_probe_path: str = "/health"


# Layer 2: Environment Variables
class EnvironmentVariables(BaseModel):
    vars: Dict[str, str] = Field(default_factory=dict)


# Layer 3: Secrets Metadata (No raw secrets exposed)
class SecretMetadata(BaseModel):
    secret_key: str
    vault_path: str
    version: int
    last_rotated_at: str  # ISO format string
    ttl_days: int
    algorithm: str = "AES-256-GCM"
    is_expired: bool = False


class SecretsLayer(BaseModel):
    secrets: Dict[str, SecretMetadata] = Field(default_factory=dict)


# Layer 4: Runtime Snapshots
class RuntimeSnapshot(BaseModel):
    timestamp: str
    active_memory_limit_mb: int
    active_cpu_limit_cores: float
    active_connections: int
    max_db_connections: int
    http_health_status: int = 200
    ssl_mode_active: str = "require"
    feature_flags_active: Dict[str, bool] = Field(default_factory=dict)
    runtime_hash: str = ""


# Full Config state for a single microservice in an environment
class ServiceEnvironmentConfig(BaseModel):
    service: MicroserviceName
    environment: Environment
    infrastructure: InfrastructureSpec
    env_vars: EnvironmentVariables
    secrets_metadata: SecretsLayer
    runtime_snapshot: RuntimeSnapshot


# Drift Finding Representation
class DriftItem(BaseModel):
    layer: str  # "Infrastructure", "EnvironmentVariables", "SecretsMetadata", "RuntimeSnapshot"
    key: str
    source_env: Environment
    target_env: Environment
    source_value: Any
    target_value: Any
    risk_level: RiskLevel
    category: str  # "Security", "Compliance", "Reliability", "Performance", "Operational"
    technical_description: str
    plain_english_summary: str
    financial_risk_estimate: str
    regulatory_impact: Optional[str] = None
    recommended_action: str


# Validation Report for a deployment attempt
class ValidationReport(BaseModel):
    report_id: str
    service: MicroserviceName
    source_env: Environment
    target_env: Environment
    generated_at: str
    total_discrepancies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    risk_score: float  # 0 to 100 (0 = safe, 100 = extreme danger)
    passed_deployment_gate: bool
    summary: str
    drifts: List[DriftItem] = Field(default_factory=list)
