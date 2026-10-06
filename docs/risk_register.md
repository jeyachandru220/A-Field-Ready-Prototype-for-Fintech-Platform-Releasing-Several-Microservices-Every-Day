# Fintech Configuration Risk Register

This risk register catalogues top configuration risk categories in daily microservice deployments, evaluating severity, likelihood, regulatory framework impact, and automated validator controls.

---

| Risk ID | Configuration Risk Description | Severity | Likelihood | Regulatory Impact | Preventive Validator Control |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RISK-01** | **Disabled DB Transport Encryption (`sslmode=disable`)** | **CRITICAL** | High | **PCI-DSS 4.1 & GDPR Art. 32** | Automated Layer 2 & 4 check blocks release if SSL mode in Prod is disabled. |
| **RISK-02** | **Expired Vault Cryptographic Key Rotation** | **CRITICAL** | High | **SOC 2 CC6.1 & PCI-DSS 3.6** | Layer 3 inspects secret TTL and rotation dates; blocks unrotated keys. |
| **RISK-03** | **Missing/Disabled Card Masking Flag (`MANDATE_STRIP_PAN=false`)** | **CRITICAL** | Medium | **PCI-DSS 3.4 (PAN Protection)** | Layer 2 semantic checker enforces compliance feature flag state. |
| **RISK-04** | **Staging Sandbox Endpoint Leaked to Production** | **CRITICAL** | High | **Fintech Bank Partner SLA** | URL inspection flags `staging`, `sandbox`, or `test` substrings in Prod. |
| **RISK-05** | **IaC Spec vs Container Runtime Memory Mismatch** | **HIGH** | Medium | **FINRA Operational Resilience** | Layer 4 cross-checks IaC limit against active pod container snapshot. |
| **RISK-06** | **Insufficient DB Connection Pool in Prod** | **HIGH** | High | **Uptime SLO (99.99%)** | Layer 2 flags pool sizes lower than staging baseline under peak load. |
| **RISK-07** | **Unencrypted HTTP Ingress Ingress Route** | **CRITICAL** | Low | **PCI-DSS 4.1 & SOC 2** | Layer 1 IaC parser verifies `ingress_tls_enabled=True`. |
| **RISK-08** | **Missing Production Vault Secret Key** | **CRITICAL** | Low | **System Availability** | Layer 3 cross-references required secret keys across environments. |
| **RISK-09** | **Verbose Debug Logging in Production** | **MEDIUM** | High | **Data Exposure Risk** | Layer 2 flags `LOG_LEVEL=DEBUG` in Production environments. |
| **RISK-10** | **Mismatched OAuth JWT Key Version** | **HIGH** | Medium | **Identity & Auth Security** | Layer 3 verifies secret version alignment between Staging and Prod. |
