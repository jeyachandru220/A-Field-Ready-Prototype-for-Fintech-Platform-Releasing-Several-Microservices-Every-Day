# Configuration Data Schemas & API Specification

The validator defines explicit schemas for each configuration layer, secrets metadata, runtime snapshots, and drift reports.

---

## 1. Infrastructure Specification Schema (Layer 1)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "InfrastructureSpec",
  "type": "object",
  "properties": {
    "cpu_request": { "type": "string", "example": "1000m" },
    "cpu_limit": { "type": "string", "example": "2000m" },
    "memory_request": { "type": "string", "example": "2Gi" },
    "memory_limit": { "type": "string", "example": "4Gi" },
    "min_replicas": { "type": "integer", "example": 4 },
    "max_replicas": { "type": "integer", "example": 16 },
    "container_port": { "type": "integer", "example": 8080 },
    "ingress_tls_enabled": { "type": "boolean", "example": true }
  },
  "required": ["cpu_limit", "memory_limit", "ingress_tls_enabled"]
}
```

---

## 2. Secrets Metadata Schema (Layer 3)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SecretMetadata",
  "type": "object",
  "properties": {
    "secret_key": { "type": "string", "example": "BANK_API_JWT_KEY" },
    "vault_path": { "type": "string", "example": "secret/data/payments/production/jwt" },
    "version": { "type": "integer", "example": 3 },
    "last_rotated_at": { "type": "string", "format": "date-time" },
    "ttl_days": { "type": "integer", "example": 30 },
    "algorithm": { "type": "string", "example": "AES-256-GCM" },
    "is_expired": { "type": "boolean", "example": false }
  },
  "required": ["secret_key", "vault_path", "version", "is_expired"]
}
```

---

## 3. Runtime Snapshot Schema (Layer 4)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RuntimeSnapshot",
  "type": "object",
  "properties": {
    "timestamp": { "type": "string", "format": "date-time" },
    "active_memory_limit_mb": { "type": "integer", "example": 4096 },
    "active_cpu_limit_cores": { "type": "number", "example": 2.0 },
    "active_connections": { "type": "integer", "example": 42 },
    "max_db_connections": { "type": "integer", "example": 100 },
    "http_health_status": { "type": "integer", "example": 200 },
    "ssl_mode_active": { "type": "string", "example": "require" },
    "feature_flags_active": {
      "type": "object",
      "additionalProperties": { "type": "boolean" }
    }
  },
  "required": ["active_memory_limit_mb", "ssl_mode_active"]
}
```

---

## 4. Drift Finding & Validation Report Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ValidationReport",
  "type": "object",
  "properties": {
    "report_id": { "type": "string", "example": "VAL-A1B2C3D4" },
    "service": { "type": "string", "enum": ["payment-processor", "ledger-core", "auth-vault", "risk-engine"] },
    "source_env": { "type": "string", "enum": ["development", "staging", "production"] },
    "target_env": { "type": "string", "enum": ["development", "staging", "production"] },
    "generated_at": { "type": "string" },
    "total_discrepancies": { "type": "integer" },
    "critical_count": { "type": "integer" },
    "high_count": { "type": "integer" },
    "medium_count": { "type": "integer" },
    "low_count": { "type": "integer" },
    "risk_score": { "type": "number", "example": 80.0 },
    "passed_deployment_gate": { "type": "boolean" },
    "summary": { "type": "string" },
    "drifts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "layer": { "type": "string" },
          "key": { "type": "string" },
          "risk_level": { "type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] },
          "category": { "type": "string" },
          "technical_description": { "type": "string" },
          "plain_english_summary": { "type": "string" },
          "financial_risk_estimate": { "type": "string" },
          "regulatory_impact": { "type": "string" },
          "recommended_action": { "type": "string" }
        }
      }
    }
  }
}
```
