"""
Environment Simulation Generator for Fintech Microservices Architecture.
Generates realistic multi-layered configurations across Dev, Staging, and Production
including non-drift clean states and explicit drift/failure scenarios.
"""

from typing import Dict, Tuple
from src.models import (
    ServiceEnvironmentConfig,
    InfrastructureSpec,
    EnvironmentVariables,
    SecretsLayer,
    SecretMetadata,
    RuntimeSnapshot,
    Environment,
    MicroserviceName
)


class EnvironmentSimulator:
    """
    Simulates environment configs for fintech microservices.
    """

    @staticmethod
    def get_service_config(
        service: MicroserviceName,
        env: Environment,
        drift_scenario: str = "none"
    ) -> ServiceEnvironmentConfig:
        """
        Returns a complete 4-layer config for a given microservice and environment.
        drift_scenario can be:
        - "none": Perfectly aligned state
        - "insecure_db": sslmode=disable leaked into Prod
        - "expired_vault_key": Vault secret key expired/unrotated in Prod
        - "memory_mismatch": IaC demands 2Gi, but active runtime container is 512Mi
        - "missing_compliance_flag": MANDATE_STRIP_PAN missing/false in Prod
        - "sandbox_url_leak": Staging bank endpoint URL leaked into Prod env vars
        """

        # Baseline Defaults per service & environment
        if env == Environment.DEVELOPMENT:
            cpu_req, cpu_lim, mem_req, mem_lim = "250m", "500m", "512Mi", "1Gi"
            min_rep, max_rep = 1, 2
        elif env == Environment.STAGING:
            cpu_req, cpu_lim, mem_req, mem_lim = "500m", "1000m", "1Gi", "2Gi"
            min_rep, max_rep = 2, 4
        else:  # PRODUCTION
            cpu_req, cpu_lim, mem_req, mem_lim = "1000m", "2000m", "2Gi", "4Gi"
            min_rep, max_rep = 4, 16

        infra = InfrastructureSpec(
            cpu_request=cpu_req,
            cpu_limit=cpu_lim,
            memory_request=mem_req,
            memory_limit=mem_lim,
            min_replicas=min_rep,
            max_replicas=max_rep,
            ingress_tls_enabled=True
        )

        # Service-specific Env Vars
        if service == MicroserviceName.PAYMENT_PROCESSOR:
            db_ssl = "disable" if env == Environment.DEVELOPMENT else "require"
            bank_url = {
                Environment.DEVELOPMENT: "https://sandbox.bank-partner.test/v1",
                Environment.STAGING: "https://staging-api.bank-partner.test/v1",
                Environment.PRODUCTION: "https://api.payments.bank.internal/v1"
            }[env]

            env_vars = EnvironmentVariables(vars={
                "ENV_NAME": env.value,
                "PAYMENT_DB_HOST": f"db-{env.value}.payments.internal",
                "PAYMENT_DB_SSLMODE": db_ssl,
                "BANK_GATEWAY_URL": bank_url,
                "MAX_DB_POOL_SIZE": "20" if env == Environment.DEVELOPMENT else ("50" if env == Environment.STAGING else "100"),
                "MANDATE_STRIP_PAN": "true",
                "ENABLE_TRANSACTION_RETRY": "true",
                "LOG_LEVEL": "DEBUG" if env == Environment.DEVELOPMENT else "INFO"
            })

            secrets = SecretsLayer(secrets={
                "PAYMENT_DB_PASSWORD": SecretMetadata(
                    secret_key="PAYMENT_DB_PASSWORD",
                    vault_path=f"secret/data/payments/{env.value}/db",
                    version=2 if env != Environment.DEVELOPMENT else 1,
                    last_rotated_at="2026-08-01T00:00:00Z",
                    ttl_days=90,
                    is_expired=False
                ),
                "BANK_API_JWT_KEY": SecretMetadata(
                    secret_key="BANK_API_JWT_KEY",
                    vault_path=f"secret/data/payments/{env.value}/jwt",
                    version=3,
                    last_rotated_at="2026-08-15T00:00:00Z",
                    ttl_days=30,
                    is_expired=False
                )
            })

            runtime = RuntimeSnapshot(
                timestamp="2026-09-07T12:00:00Z",
                active_memory_limit_mb=4096 if env == Environment.PRODUCTION else (2048 if env == Environment.STAGING else 1024),
                active_cpu_limit_cores=2.0 if env == Environment.PRODUCTION else 1.0,
                active_connections=42,
                max_db_connections=100 if env == Environment.PRODUCTION else 50,
                ssl_mode_active=db_ssl,
                feature_flags_active={"MANDATE_STRIP_PAN": True, "PAYMENT_2FA": True}
            )

        elif service == MicroserviceName.LEDGER_CORE:
            env_vars = EnvironmentVariables(vars={
                "ENV_NAME": env.value,
                "LEDGER_DB_HOST": f"ledger-db-{env.value}.internal",
                "LEDGER_DB_SSLMODE": "require",
                "DOUBLE_ENTRY_AUDIT_STRICT": "true",
                "MAX_BATCH_SIZE": "5000",
                "LOG_LEVEL": "INFO"
            })
            secrets = SecretsLayer(secrets={
                "LEDGER_CRYPTO_SIGNING_KEY": SecretMetadata(
                    secret_key="LEDGER_CRYPTO_SIGNING_KEY",
                    vault_path=f"secret/data/ledger/{env.value}/hsm",
                    version=1,
                    last_rotated_at="2026-07-01T00:00:00Z",
                    ttl_days=180,
                    is_expired=False
                )
            })
            runtime = RuntimeSnapshot(
                timestamp="2026-09-07T12:00:00Z",
                active_memory_limit_mb=4096 if env == Environment.PRODUCTION else 2048,
                active_cpu_limit_cores=4.0 if env == Environment.PRODUCTION else 2.0,
                active_connections=120,
                max_db_connections=200,
                ssl_mode_active="require",
                feature_flags_active={"DOUBLE_ENTRY_AUDIT_STRICT": True}
            )

        elif service == MicroserviceName.AUTH_VAULT:
            env_vars = EnvironmentVariables(vars={
                "ENV_NAME": env.value,
                "AUTH_VAULT_URL": f"https://vault-{env.value}.auth.internal",
                "TOKEN_TTL_SECONDS": "900",
                "ENFORCE_MFA": "true",
                "MAX_FAILED_ATTEMPTS": "5"
            })
            secrets = SecretsLayer(secrets={
                "OAUTH_PRIVATE_KEY": SecretMetadata(
                    secret_key="OAUTH_PRIVATE_KEY",
                    vault_path=f"secret/data/auth/{env.value}/rsa",
                    version=4,
                    last_rotated_at="2026-08-20T00:00:00Z",
                    ttl_days=30,
                    is_expired=False
                )
            })
            runtime = RuntimeSnapshot(
                timestamp="2026-09-07T12:00:00Z",
                active_memory_limit_mb=4096 if env == Environment.PRODUCTION else 2048,
                active_cpu_limit_cores=2.0 if env == Environment.PRODUCTION else 1.0,
                active_connections=350,
                max_db_connections=500,
                ssl_mode_active="require",
                feature_flags_active={"ENFORCE_MFA": True}
            )

        else:  # RISK_ENGINE
            env_vars = EnvironmentVariables(vars={
                "ENV_NAME": env.value,
                "FRAUD_MODEL_VERSION": "v4.2.1",
                "FRAUD_SCORE_THRESHOLD": "0.85",
                "RISK_DB_HOST": f"risk-db-{env.value}.internal",
                "RISK_DB_SSLMODE": "require"
            })
            secrets = SecretsLayer(secrets={
                "MODEL_DECRYPTION_KEY": SecretMetadata(
                    secret_key="MODEL_DECRYPTION_KEY",
                    vault_path=f"secret/data/risk/{env.value}/ml",
                    version=2,
                    last_rotated_at="2026-08-10T00:00:00Z",
                    ttl_days=60,
                    is_expired=False
                )
            })
            runtime = RuntimeSnapshot(
                timestamp="2026-09-07T12:00:00Z",
                active_memory_limit_mb=4096 if env == Environment.PRODUCTION else 2048,
                active_cpu_limit_cores=2.0 if env == Environment.PRODUCTION else 1.0,
                active_connections=80,
                max_db_connections=150,
                ssl_mode_active="require",
                feature_flags_active={"FRAUD_MODEL_ACTIVE": True}
            )

        # APPLY DRIFT SCENARIOS if specified and target is PRODUCTION
        if env == Environment.PRODUCTION and drift_scenario != "none":
            if drift_scenario == "insecure_db":
                env_vars.vars["PAYMENT_DB_SSLMODE"] = "disable"
                runtime.ssl_mode_active = "disable"

            elif drift_scenario == "expired_vault_key":
                if "BANK_API_JWT_KEY" in secrets.secrets:
                    secrets.secrets["BANK_API_JWT_KEY"].is_expired = True
                    secrets.secrets["BANK_API_JWT_KEY"].last_rotated_at = "2026-05-01T00:00:00Z"
                elif "LEDGER_CRYPTO_SIGNING_KEY" in secrets.secrets:
                    secrets.secrets["LEDGER_CRYPTO_SIGNING_KEY"].is_expired = True
                elif "OAUTH_PRIVATE_KEY" in secrets.secrets:
                    secrets.secrets["OAUTH_PRIVATE_KEY"].is_expired = True

            elif drift_scenario == "memory_mismatch":
                # IaC demands 4Gi (4096MB), but active container is capped at 512MB
                infra.memory_limit = "4Gi"
                runtime.active_memory_limit_mb = 512

            elif drift_scenario == "missing_compliance_flag":
                env_vars.vars["MANDATE_STRIP_PAN"] = "false"
                runtime.feature_flags_active["MANDATE_STRIP_PAN"] = False

            elif drift_scenario == "sandbox_url_leak":
                env_vars.vars["BANK_GATEWAY_URL"] = "https://staging-api.bank-partner.test/v1"

        return ServiceEnvironmentConfig(
            service=service,
            environment=env,
            infrastructure=infra,
            env_vars=env_vars,
            secrets_metadata=secrets,
            runtime_snapshot=runtime
        )
