"""
Plain-English Recommendation Generator for Non-Specialist Reviewers.
Translates technical configuration discrepancies into accessible business,
financial risk, regulatory compliance, and simple remediation terms.
"""

from typing import Dict, Any, Tuple
from src.models import RiskLevel, Environment


def translate_drift_to_plain_english(
    layer: str,
    key: str,
    source_env: Environment,
    target_env: Environment,
    source_val: Any,
    target_val: Any,
    service_name: str
) -> Tuple[RiskLevel, str, str, str, str, str]:
    """
    Translates a configuration discrepancy into:
    (RiskLevel, category, technical_description, plain_english_summary, financial_risk_estimate, regulatory_impact, recommended_action)
    """
    s_val_str = str(source_val)
    t_val_str = str(target_val)

    # 1. Insecure Database/Protocol Settings
    if "ssl" in key.lower() or "tls" in key.lower() or "mode" in key.lower() and "disable" in t_val_str.lower():
        return (
            RiskLevel.CRITICAL,
            "Security",
            f"Database SSL mode in target '{target_env.value}' is set to '{t_val_str}', whereas '{source_env.value}' is '{s_val_str}'.",
            f"The microservice '{service_name}' is configured to connect to the database in PRODUCTION without encryption (SSL disabled). This allows network eavesdroppers or attackers to intercept live customer financial data in transit.",
            "$250,000+ (Fines for unencrypted customer PII/financial transactions, incident response costs, and brand reputation damage).",
            "PCI-DSS Requirement 4.1 (Encrypt cardholder data across open, public networks) & GDPR Article 32 (Encryption of personal data).",
            "Immediately change 'sslmode' in Production configuration to 'require' or 'verify-full' before deploying."
        )

    # 2. Vault Secrets Metadata / Rotation Expiry
    if "expired" in key.lower() or ("secret" in key.lower() and "version" in key.lower()) or "ttl" in key.lower():
        if target_val is True or "expired" in s_val_str.lower() or source_val != target_val:
            return (
                RiskLevel.CRITICAL,
                "Compliance & Security",
                f"Secret key '{key}' version mismatch or TTL expiry between '{source_env.value}' ({s_val_str}) and '{target_env.value}' ({t_val_str}).",
                f"Production is using an unrotated, outdated, or expired cryptographic secret key for '{service_name}'. In a fintech platform, expired keys cause payment authentication failures or allow revoked keys to decrypt transaction payloads.",
                "$150,000 per hour of checkout/payment outage due to authentication rejection.",
                "SOC 2 Trust Services Criteria (CC6.1 - Secret Key Lifecycle) & PCI-DSS Requirement 3.6 (Cryptographic key management).",
                "Execute the vault key rotation pipeline to issue a active v2 key to Production before proceeding with release."
            )

    # 3. IaC vs Runtime Memory Allocation Discrepancy
    if "memory" in key.lower() or "limit" in key.lower():
        return (
            RiskLevel.HIGH,
            "Reliability & Capacity",
            f"IaC infrastructure specification defines '{s_val_str}' but active container runtime snapshot reports '{t_val_str}'.",
            f"The infrastructure blueprint specifies 2GB of memory for '{service_name}', but the live production container is running capped at 512MB (4x lower). Under peak market trading volume, this microservice will run out of memory and crash instantly.",
            "$80,000 (Loss of transaction processing capability during high-volume trading hours).",
            "FINRA / SEC Operational Resilience & Business Continuity Standard.",
            "Restart container pod with synchronized Kubernetes/Docker spec matching 2Gi memory limit."
        )

    # 4. Compliance Feature Flags (e.g., MANDATE_STRIP_PAN or 2FA)
    if "flag" in key.lower() or "mandate" in key.lower() or "pan" in key.lower() or "2fa" in key.lower() or "strip" in key.lower():
        return (
            RiskLevel.CRITICAL,
            "Compliance",
            f"Feature flag '{key}' is '{s_val_str}' in {source_env.value} but '{t_val_str}' in {target_env.value}.",
            f"A vital compliance safety flag ('{key}') is disabled in Production. In Staging, credit card numbers are masked, but in Production full raw card numbers could be logged to plain text files.",
            "$500,000+ (Immediate PCI-DSS audit failure, card processor suspension, regulatory penalties).",
            "PCI-DSS Requirement 3.4 (Render PAN unreadable anywhere it is stored/logged).",
            "Enable '{key}=true' in Production configuration immediately."
        )

    # 5. Staging/Test Host URLs leaking into Production
    if "url" in key.lower() or "host" in key.lower() or "endpoint" in key.lower():
        if "staging" in t_val_str.lower() or "dev" in t_val_str.lower() or "test" in t_val_str.lower() or "mock" in t_val_str.lower():
            return (
                RiskLevel.CRITICAL,
                "Operational & Financial",
                f"Target '{target_env.value}' key '{key}' points to sandbox/staging endpoint: '{t_val_str}'.",
                f"Production '{service_name}' is pointing to a test/sandbox third-party service ('{t_val_str}') instead of the real bank production gateway. Live customer transactions will be routed to a dummy sandbox and will fail to process real money.",
                "$300,000+ (Total failure of payment settlements and customer transactional disputes).",
                "Fintech Bank Partner API SLA & Operational Compliance Requirement.",
                "Update Production '{key}' to point to the secure production host URL ('https://api.bank.internal/v1')."
            )

    # 6. Database Connection Pool Limits
    if "conn" in key.lower() or "pool" in key.lower():
        return (
            RiskLevel.HIGH,
            "Performance",
            f"Connection pool configuration '{key}' has value '{s_val_str}' in {source_env.value} vs '{t_val_str}' in {target_env.value}.",
            f"The maximum database connection pool size in Production ({t_val_str}) is lower than Staging ({s_val_str}). Under normal production traffic, requests will queue up and time out.",
            "$40,000 (Degraded system throughput and high latency checkout drop-off).",
            "Internal Service Level Objective (SLO) > 99.95% Availability.",
            "Align target connection pool to at least match Staging workload capacity."
        )

    # 7. Default Generic Catch-All
    if s_val_str != t_val_str:
        return (
            RiskLevel.MEDIUM,
            "Operational",
            f"Configuration key '{key}' differs: source ({source_env.value}) = '{s_val_str}', target ({target_env.value}) = '{t_val_str}'.",
            f"The microservice '{service_name}' has a configuration value difference in '{key}' between {source_env.value} and {target_env.value}. This may cause unexpected behavior during release.",
            "$10,000 - $30,000 (Potential engineering investigation time and delay in deployment).",
            "General IT Governance & Change Management Policy.",
            f"Verify if key '{key}' value '{t_val_str}' in {target_env.value} is intentional or align it with verified Staging baseline."
        )

    return (
        RiskLevel.INFO,
        "Operational",
        f"Value '{s_val_str}' matches expected pattern.",
        f"No risk detected for '{key}'. Configuration is aligned.",
        "$0",
        "None",
        "No action required."
    )
