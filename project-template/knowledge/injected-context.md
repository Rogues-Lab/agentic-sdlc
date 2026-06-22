# Injected Knowledge Context

major_project_id: openclaw-platform
product_id: clawsweeper
repos: film-fun/community, film-fun/splice, openclaw/clawsweeper
deployments: community-web-prod, splice-api-prod, splice-worker-prod
change_bundle_ids: CHG-001
tags: hotfix

## Applied Rules
- base-shared (priority=100)
- openclaw-major-project (priority=200)
- clawsweeper-repo (priority=300)
- film-fun-community-repo (priority=300)
- prod-deployment-hardening (priority=500)
- hotfix-policy (priority=600)

## Decision Context
```json
{
  "quality_gates": {
    "required_check_types": [
      "unit",
      "integration"
    ],
    "blocked_on_review_severity": [
      "high",
      "critical"
    ],
    "blocked_on_qa_severity": [
      "high",
      "critical"
    ]
  },
  "architecture": {
    "strategy": "modular-agent-runtime",
    "constraints": [
      "backward-compatible agent contracts"
    ]
  },
  "release": {
    "requires_canary": true,
    "requires_rollback_plan": true,
    "expedite": true,
    "post_release_review_required": true
  },
  "priority": {
    "weights": {
      "time_criticality": 2.0
    },
    "blocked_penalty": 400
  }
}
```

## Module: shared-standards
source: project-template/knowledge/shared/engineering-standards.md

# Engineering Standards

- Deterministic APIs: stable error envelopes and explicit versioning.
- Feature flags for risky rollout paths.
- Contract-first integration updates.
- Mandatory traceability from requirement to tests.

## Module: openclaw-architecture
source: project-template/knowledge/openclaw/architecture.md

# OpenClaw Architecture Guidelines

- Keep orchestration logic deterministic and auditable.
- Separate adapter ingestion from decision logic.
- Preserve source-system traceability in all transforms.

## Module: clawsweeper-standards
source: project-template/knowledge/openclaw/clawsweeper-standards.md

# Clawsweeper Repo Standards

- Stable report schemas for run outputs.
- Include trace IDs in all generated reports.
- Keep automation scripts idempotent where possible.

## Module: community-contracts
source: project-template/knowledge/film-fun/community-contracts.md

# Community Contracts

- Auth payload includes user_id, tenant_id, roles, and trace_id.
- Backward compatibility: do not remove fields without a deprecation period.

