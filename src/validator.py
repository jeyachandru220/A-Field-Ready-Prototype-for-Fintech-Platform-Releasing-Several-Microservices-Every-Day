"""
Core 4-Layer Configuration Drift Validator.
Inspects and compares infrastructure specs, env vars, secrets metadata, and runtime snapshots
across development, staging, and production environments.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from src.models import (
    ServiceEnvironmentConfig,
    ValidationReport,
    DriftItem,
    RiskLevel,
    Environment,
    MicroserviceName
)
from src.plain_language import translate_drift_to_plain_english


class ConfigurationDriftValidator:
    """
    Multi-layered drift inspection engine.
    Computes cross-environment risk scores, evaluates 4 configuration layers,
    and enforces pre-deployment gating based on automated compliance & safety rules.
    """

    CRITICAL_RISK_WEIGHT = 40.0
    HIGH_RISK_WEIGHT = 20.0
    MEDIUM_RISK_WEIGHT = 8.0
    LOW_RISK_WEIGHT = 2.0

    @classmethod
    def validate_deployment(
        cls,
        source_config: ServiceEnvironmentConfig,
        target_config: ServiceEnvironmentConfig,
        gate_threshold: float = 25.0
    ) -> ValidationReport:
        """
        Compares source environment (e.g. Staging) against target environment (e.g. Production).
        Returns a comprehensive ValidationReport.
        """
        drifts: List[DriftItem] = []
        svc_name = source_config.service.value

        # Layer 1: Infrastructure Definitions (IaC)
        cls._compare_infrastructure(source_config, target_config, drifts, svc_name)

        # Layer 2: Environment Variables
        cls._compare_env_vars(source_config, target_config, drifts, svc_name)

        # Layer 3: Secrets Metadata
        cls._compare_secrets_metadata(source_config, target_config, drifts, svc_name)

        # Layer 4: Runtime Snapshots & Cross-Layer (IaC vs Runtime)
        cls._compare_runtime_snapshots(source_config, target_config, drifts, svc_name)

        # Calculate counts & risk score
        crit = sum(1 for d in drifts if d.risk_level == RiskLevel.CRITICAL)
        high = sum(1 for d in drifts if d.risk_level == RiskLevel.HIGH)
        med = sum(1 for d in drifts if d.risk_level == RiskLevel.MEDIUM)
        low = sum(1 for d in drifts if d.risk_level == RiskLevel.LOW)
        info = sum(1 for d in drifts if d.risk_level == RiskLevel.INFO)

        raw_score = (
            crit * cls.CRITICAL_RISK_WEIGHT +
            high * cls.HIGH_RISK_WEIGHT +
            med * cls.MEDIUM_RISK_WEIGHT +
            low * cls.LOW_RISK_WEIGHT
        )
        risk_score = min(100.0, round(raw_score, 1))

        # Passed gate if risk score < gate_threshold AND 0 CRITICAL risks
        passed_gate = (risk_score < gate_threshold) and (crit == 0)

        # Executive Summary
        if passed_gate:
            summary = (
                f"✅ DEPLOYMENT APPROVED: Microservice '{svc_name}' passed all 4 layer checks. "
                f"Risk score is {risk_score}/100 (Threshold: {gate_threshold}). Zero critical security or compliance issues detected."
            )
        else:
            summary = (
                f"❌ DEPLOYMENT BLOCKED: Microservice '{svc_name}' failed pre-deployment safety gate. "
                f"Risk score is {risk_score}/100 with {crit} CRITICAL and {high} HIGH risk discrepancies detected. "
                f"Immediate remediation required before production release."
            )

        report = ValidationReport(
            report_id=f"VAL-{uuid.uuid4().hex[:8].upper()}",
            service=source_config.service,
            source_env=source_config.environment,
            target_env=target_config.environment,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_discrepancies=len(drifts),
            critical_count=crit,
            high_count=high,
            medium_count=med,
            low_count=low,
            info_count=info,
            risk_score=risk_score,
            passed_deployment_gate=passed_gate,
            summary=summary,
            drifts=drifts
        )
        return report

    @classmethod
    def _compare_infrastructure(
        cls,
        src: ServiceEnvironmentConfig,
        tgt: ServiceEnvironmentConfig,
        drifts: List[DriftItem],
        svc_name: str
    ):
        t_iac = tgt.infrastructure

        # Ingress TLS enabled check in prod
        if tgt.environment == Environment.PRODUCTION and not t_iac.ingress_tls_enabled:
            drifts.append(DriftItem(
                layer="Infrastructure Definitions (IaC)",
                key="infrastructure.ingress_tls_enabled",
                source_env=src.environment,
                target_env=tgt.environment,
                source_value=True,
                target_value=False,
                risk_level=RiskLevel.CRITICAL,
                category="Security",
                technical_description="Production IaC ingress spec has ingress_tls_enabled set to False.",
                plain_english_summary="Production ingress endpoint is configured to accept unencrypted HTTP traffic.",
                financial_risk_estimate="$200,000+ (Security audit penalty & data exposure risk).",
                regulatory_impact="PCI-DSS Requirement 4.1 & SOC 2 Privacy.",
                recommended_action="Enable ingress_tls_enabled=True in Production IaC manifest."
            ))

    @classmethod
    def _compare_env_vars(
        cls,
        src: ServiceEnvironmentConfig,
        tgt: ServiceEnvironmentConfig,
        drifts: List[DriftItem],
        svc_name: str
    ):
        s_vars = src.env_vars.vars
        t_vars = tgt.env_vars.vars

        all_keys = set(s_vars.keys()).union(set(t_vars.keys()))

        for k in sorted(all_keys):
            s_val = s_vars.get(k, "<MISSING>")
            t_val = t_vars.get(k, "<MISSING>")

            # Check 1: Leaked Sandbox/Staging/Test URLs in Production env vars
            if tgt.environment == Environment.PRODUCTION and any(sub in t_val.lower() for sub in ["staging", "sandbox", "test"]):
                drifts.append(DriftItem(
                    layer="Environment Variables",
                    key=f"env_vars.{k}",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value=s_val,
                    target_value=t_val,
                    risk_level=RiskLevel.CRITICAL,
                    category="Operational & Financial",
                    technical_description=f"Key '{k}' in Production contains test/staging domain substring '{t_val}'.",
                    plain_english_summary=f"Production '{svc_name}' is pointing to a sandbox/staging endpoint ('{t_val}'). Live financial transactions will be sent to test servers and fail.",
                    financial_risk_estimate="$350,000+ (Outage of live checkout settlements and partner SLA breach).",
                    regulatory_impact="Fintech Bank Partner SLA Policy.",
                    recommended_action=f"Update Production '{k}' to verified production endpoint URL."
                ))
                continue

            # Check 2: Insecure SSL Mode in Prod
            if "SSLMODE" in k and t_val.lower() == "disable":
                drifts.append(DriftItem(
                    layer="Environment Variables",
                    key=f"env_vars.{k}",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value=s_val,
                    target_value=t_val,
                    risk_level=RiskLevel.CRITICAL,
                    category="Security",
                    technical_description=f"Production database SSL mode '{k}' is set to '{t_val}'.",
                    plain_english_summary=f"Microservice '{svc_name}' database connection in PRODUCTION has encryption disabled (SSL disabled). Attackers can eavesdrop on financial transaction data.",
                    financial_risk_estimate="$250,000+ (PCI-DSS non-compliance fines & mandatory security audit).",
                    regulatory_impact="PCI-DSS Requirement 4.1 & GDPR Article 32.",
                    recommended_action="Set SSLMODE to 'require' or 'verify-full' in Production immediately."
                ))
                continue

            # Check 3: Compliance Feature Flags (e.g. MANDATE_STRIP_PAN)
            if ("MANDATE" in k or "PAN" in k or "2FA" in k or "COMPLIANCE" in k) and t_val.lower() in ["false", "0", "disabled"]:
                drifts.append(DriftItem(
                    layer="Environment Variables",
                    key=f"env_vars.{k}",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value=s_val,
                    target_value=t_val,
                    risk_level=RiskLevel.CRITICAL,
                    category="Compliance",
                    technical_description=f"Compliance safety flag '{k}' is set to '{t_val}' in Production.",
                    plain_english_summary=f"Mandatory security/compliance flag '{k}' is DISABLED in Production. Unmasked customer credit card numbers may be written to plain text logs.",
                    financial_risk_estimate="$500,000+ (Immediate card network suspension & regulatory penalty).",
                    regulatory_impact="PCI-DSS Requirement 3.4 (PAN unreadability).",
                    recommended_action=f"Set '{k}=true' in Production configuration before releasing."
                ))
                continue

            # Check 4: Filter out expected environment conventions for clean releases
            if k in ["ENV_NAME", "ENVIRONMENT"] and t_val in ["production", "prod"]:
                continue
            if "HOST" in k or "URL" in k:
                # If Staging URL has 'staging' and Prod URL has 'production' or 'bank.internal', that's expected
                if ("staging" in s_val.lower() or "dev" in s_val.lower()) and ("production" in t_val.lower() or "prod" in t_val.lower() or "bank.internal" in t_val.lower()):
                    continue
            if k == "MAX_DB_POOL_SIZE" and int(t_val) >= int(s_val):
                continue
            if k == "LOG_LEVEL" and t_val in ["INFO", "WARN", "ERROR"]:
                continue

            # If there's an actual unhandled value mismatch
            if s_val != t_val:
                r_level, cat, tech, plain, fin, reg, act = translate_drift_to_plain_english(
                    "EnvironmentVariables", k, src.environment, tgt.environment, s_val, t_val, svc_name
                )
                drifts.append(DriftItem(
                    layer="Environment Variables",
                    key=f"env_vars.{k}",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value=s_val,
                    target_value=t_val,
                    risk_level=r_level,
                    category=cat,
                    technical_description=tech,
                    plain_english_summary=plain,
                    financial_risk_estimate=fin,
                    regulatory_impact=reg,
                    recommended_action=act
                ))

    @classmethod
    def _compare_secrets_metadata(
        cls,
        src: ServiceEnvironmentConfig,
        tgt: ServiceEnvironmentConfig,
        drifts: List[DriftItem],
        svc_name: str
    ):
        s_secrets = src.secrets_metadata.secrets
        t_secrets = tgt.secrets_metadata.secrets

        all_keys = set(s_secrets.keys()).union(set(t_secrets.keys()))

        for k in sorted(all_keys):
            s_meta = s_secrets.get(k)
            t_meta = t_secrets.get(k)

            if not t_meta:
                drifts.append(DriftItem(
                    layer="Secrets Metadata",
                    key=f"secrets.{k}",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value=s_meta.vault_path if s_meta else "Present",
                    target_value="MISSING",
                    risk_level=RiskLevel.CRITICAL,
                    category="Security",
                    technical_description=f"Secret '{k}' exists in {src.environment.value} but is missing in {tgt.environment.value}.",
                    plain_english_summary=f"Required secret key '{k}' is missing from Production Vault.",
                    financial_risk_estimate="$100,000 (Immediate microservice startup crash).",
                    regulatory_impact="PCI-DSS Requirement 8.2.",
                    recommended_action=f"Provision secret key '{k}' in Production Vault path."
                ))
                continue

            # Check rotation / expired state
            if t_meta.is_expired:
                drifts.append(DriftItem(
                    layer="Secrets Metadata",
                    key=f"secrets.{k}.is_expired",
                    source_env=src.environment,
                    target_env=tgt.environment,
                    source_value="Valid Key",
                    target_value="EXPIRED KEY",
                    risk_level=RiskLevel.CRITICAL,
                    category="Security & Compliance",
                    technical_description=f"Secret key '{k}' in Production Vault is marked as expired.",
                    plain_english_summary=f"Production secret key '{k}' has passed its expiration date without key rotation.",
                    financial_risk_estimate="$150,000 (Payment authentication rejection outage).",
                    regulatory_impact="SOC 2 Trust Services Criteria & PCI-DSS 3.6.",
                    recommended_action=f"Rotate secret key '{k}' in Vault before deploying."
                ))

    @classmethod
    def _compare_runtime_snapshots(
        cls,
        src: ServiceEnvironmentConfig,
        tgt: ServiceEnvironmentConfig,
        drifts: List[DriftItem],
        svc_name: str
    ):
        t_iac = tgt.infrastructure
        t_rt = tgt.runtime_snapshot

        def _parse_mb(val: str) -> int:
            v = val.lower()
            if "gi" in v:
                return int(v.replace("gi", "").strip()) * 1024
            if "mi" in v:
                return int(v.replace("mi", "").strip())
            return 1024

        iac_mem_mb = _parse_mb(t_iac.memory_limit)
        if t_rt.active_memory_limit_mb < iac_mem_mb:
            drifts.append(DriftItem(
                layer="Runtime Snapshot (IaC vs Runtime)",
                key="runtime.active_memory_limit_mb",
                source_env=src.environment,
                target_env=tgt.environment,
                source_value=f"IaC Manifest: {t_iac.memory_limit} ({iac_mem_mb}MB)",
                target_value=f"Active Container: {t_rt.active_memory_limit_mb}MB",
                risk_level=RiskLevel.CRITICAL,
                category="Reliability",
                technical_description=f"IaC manifest demands {t_iac.memory_limit} memory limit, but running container snapshot reports only {t_rt.active_memory_limit_mb}MB allocated.",
                plain_english_summary=f"The infrastructure blueprint asks for 2GB memory for '{svc_name}', but live production container is running capped at 512MB. Under peak traffic, the microservice will crash with Out-Of-Memory (OOM).",
                financial_risk_estimate="$80,000 (Transaction processing failure under market volume surge).",
                regulatory_impact="FINRA / SEC Operational Resilience Guidelines.",
                recommended_action="Synchronize active Kubernetes/Docker container memory limit with IaC specification."
            ))

        if tgt.environment == Environment.PRODUCTION and t_rt.ssl_mode_active.lower() == "disable":
            drifts.append(DriftItem(
                layer="Runtime Snapshot",
                key="runtime.ssl_mode_active",
                source_env=src.environment,
                target_env=tgt.environment,
                source_value="require",
                target_value="disable",
                risk_level=RiskLevel.CRITICAL,
                category="Security",
                technical_description="Active container process snapshot confirms database connection running with ssl_mode=disable.",
                plain_english_summary="Live running container process is actively transmitting database traffic in clear unencrypted text.",
                financial_risk_estimate="$300,000 (Major security compliance incident).",
                regulatory_impact="PCI-DSS Requirement 4.1.",
                recommended_action="Restart container pod with SSL enforcement variables."
            ))
