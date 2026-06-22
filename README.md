# Agentic SDLC Project (OpenClaw)

Portable, project-agnostic, automation-first SDLC system for custom software delivery with OpenClaw agents.

This project is intended to be copied into other OpenClaw instances or shared as a standalone pack.

## What This Solves

- Deterministic delivery lifecycle: `goal -> design -> build -> test -> review -> QA -> ship`
- Machine-checkable traceability between requirements, acceptance criteria, tests, tickets, and checks
- Policy-driven ship decisions
- External visibility via backlog sync adapters (GitHub/Jira/Linear style mappings)
- Priority-based CTO scheduling

## Core Concepts

Stable IDs are mandatory:
- `SPEC-*` (spec)
- `REQ-*` (requirement)
- `AC-*` (acceptance criterion)
- `TKT-*` (ticket)
- `TEST-*` (test)
- `CHECK-*` (verification check)
- `RVW-*` / `QA-*` (review + QA report)

## Project Layout

- `templates/` - human + machine templates
- `schemas/` - JSON schemas for artifact validation
- `scripts/` - runnable automation (`validate`, `verify`, `gate`, `sync`, `schedule`, `bootstrap`, `export`)
- `mappings/` - field mappings for external systems
- `adapters/` - adapter contracts/docs
- `policies/` - priority policy (WSJF)
- `automation/` - OpenClaw integration examples (taskflow/cron/hooks)
- `project-template/` - working starter project

## Quick Start

```bash
cd agentic-sdlc-pack
make validate
make verify
make gate
make sync-backlog
make sync-github-project
make enrich-portfolio
make schedule-backlog
# or one command
make sync-and-plan
```

Outputs:
- `project-template/reports/verification-results.json`
- `project-template/reports/ship-decision.json`
- `project-template/backlog/ranked-backlog.json`

## Reuse in Another Instance

```bash
# create a new feature workspace from starter
./scripts/bootstrap_project.sh /path/to/new-feature

# or package for sharing
./scripts/export_pack.sh
```

Then in target instance:
1. copy/extract pack
2. edit `artifacts/*.json`, `reports/*.json`, `policies/*.json`
3. run scripts directly or via `make`

## External System Visibility

Canonical source key is: `(source.system, source.scope, source.external_id)`.
This prevents collisions when a single GitHub Project spans multiple repositories that reuse issue numbers.

GitHub Issues sync (single repo or mixed exports):

Use `scripts/sync_backlog.py` to sync external items into canonical backlog:

```bash
python3 scripts/sync_backlog.py \
  --external-items project-template/backlog/github-issues.sample.json \
  --mapping mappings/github.mapping.json \
  --backlog project-template/backlog/backlog.json
```


GitHub Project sync (multi-repo):

```bash
python3 scripts/sync_github_project.py \
  --project-export project-template/backlog/github-project.sample.json \
  --backlog project-template/backlog/backlog.json
```

Then schedule:

```bash
python3 scripts/schedule_backlog.py \
  --backlog project-template/backlog/backlog.json \
  --policy policies/priority-policy.json \
  --out project-template/backlog/ranked-backlog.json
```

### Command Center Kanban Sync

If your team tracks work in Command Center boards, sync cards into the canonical backlog:

```bash
make sync-command-center-board
```

Files used:
- `project-template/backlog/command-center-kanban.sample.json`
- `mappings/command-center-kanban.mapping.json`

For production, replace the sample export with your board export payload and keep the same mapping contract.

## Portfolio Model (Major Projects -> Repos)

One major project can contain many repositories.

Examples included:
- `openclaw-platform` -> `openclaw/clawsweeper`
- `film-fun-ecosystem` -> `film-fun/community`, `film-fun/splice`, `film-fun/reelkit`

Portfolio source file:
- `project-template/portfolio/projects.json`

After syncing external items, enrich backlog with major project links:

```bash
python3 scripts/enrich_backlog_with_portfolio.py \
  --backlog project-template/backlog/backlog.json \
  --portfolio project-template/portfolio/projects.json \
  --out project-template/backlog/backlog.json
```

Then scheduling output includes:
- ranked backlog items
- ranked major projects
- ranked repos


## Multi-Change and Cross-Deployment Model

Use change bundles for discrete and composite changes:
- one feature can map to one change bundle
- one major initiative can include multiple change bundles
- each change bundle can span many repos and deployments

Source file:
- `project-template/change-bundles/change-bundles.json`

Plan bundles:

```bash
python3 scripts/plan_change_bundles.py \
  --change-bundles project-template/change-bundles/change-bundles.json \
  --out project-template/change-bundles/ranked-change-bundles.json
```


## Deterministic Release Gates

Gate decision is automated by policy:

```bash
python3 scripts/evaluate_ship_gate.py \
  --policy project-template/policies/gate-policy.json \
  --verification-results project-template/reports/verification-results.json \
  --review-report project-template/reports/review-report.json \
  --qa-report project-template/reports/qa-report.json \
  --out project-template/reports/ship-decision.json
```

Ship is blocked if:
- required gates are not `PASS`
- blocked check types fail (security/contract/integration by policy)
- open high/critical review findings or QA defects exist
- the review report's `decision` is not `APPROVE`
- the three artifacts disagree on which spec they describe (identity cross-check)

Only unresolved QA defects (`open`/`reopened`) block; defects marked `fixed`/`resolved` do not.

Gate provenance (which artifact each required gate is read from):
- `test_ready` is **computed** by `run_verification.py` from actual check results.
- `review_ready` is derived from the review report's `decision` + `gates.review_ready`.
- `qa_ready` is derived from the QA report's `gates.qa_ready`.
- `design_ready` and `build_ready` are **externally-asserted inputs** supplied in the
  verification manifest — the pack does not compute them. Treat them as attestations
  produced by an upstream step, not as machine-verified facts.

### Waivers (deliberate, time-boxed risk acceptance)

When `waiver_policy.allowed` is true, waivers listed under `waivers` in the verification
results can un-block a specific reason. A waiver is honored only if it carries every field
in `required_fields` and its `expires_at` is in the future. Each waiver targets a reason by
`gate`, `check_id`, `check_type`, or explicit reason `code`. Honored and ignored waivers are
recorded in the ship decision (`waived`, `invalid_waivers`).

### Regression Tests

```bash
make test-gate
```

## Dynamic Knowledge Module Injection

Standards, architecture, and deployment guidelines are dynamically injected from a knowledge registry instead of hard-coded in prompts.

Registry file:
- `project-template/knowledge/module-registry.json`

Inject relevant modules by major project + repos + change bundles:

```bash
python3 scripts/resolve_knowledge_context.py \
  --registry project-template/knowledge/module-registry.json \
  --major-project-id film-fun-ecosystem \
  --change-bundles project-template/change-bundles/change-bundles.json \
  --out-json project-template/knowledge/injected-context.json \
  --out-md project-template/knowledge/injected-context.md
```


## OpenClaw Automation Integration

Example config files:
- `automation/taskflow-feature-delivery.example.yaml`
- `automation/cron-regression.example.yaml`
- `automation/hooks.example.yaml`

These show how to wire lifecycle stages into OpenClaw taskflow/cron/hooks.

Coding execution policy:
- route implementation through ACP subscription workers (`codex` or `claude`)
- require lifecycle hooks (`delegation.requested` -> `review.completed`)
- do not run direct model-only coding for implementation tickets.

## Resolver Pattern (Project-Agnostic Context)

The SDLC core stays generic. Product/project specifics are loaded at runtime via resolver rules.

Resolver supports selectors for:
- `major_project_id`
- `product_id`
- `repos` (exact, prefix, glob)
- `deployment_targets`
- `change_bundle_ids`
- `tags` (for dynamic modes like `hotfix`)

Rules are deterministic:
- sorted by `(priority, id)`
- modules are de-duplicated by `id`
- `decision_overrides` are deep-merged in order

Run:

```bash
make inject-knowledge \
  MAJOR_PROJECT_ID=openclaw-platform \
  PRODUCT_ID=clawsweeper \
  REPOS=openclaw/clawsweeper \
  TAGS=hotfix
```

Outputs:
- `project-template/knowledge/injected-context.json`
- `project-template/knowledge/injected-context.md`

## Context-Driven Automation

The injected `decision_context` can directly drive automation:

```bash
# context-aware ranking
make schedule-backlog

# context-aware gate decision
make gate-with-context
```

Examples:
- hotfix can increase time-criticality weight
- production deployments can force stricter release constraints
- project/repo context can tighten quality gate requirements

## Spec Kit Alignment (github/spec-kit)

This pack now mirrors key Spec Kit strengths while keeping OpenClaw multi-repo orchestration:
- spec-first lifecycle (`spec -> plan -> tasks -> implement`) remains central
- constitutional/standards guidance is externalized as runtime-resolved modules
- template/command override concept is reflected via resolver rules and priorities
- deterministic gates/checklists are enforced by machine-readable artifacts and scripts

Recommended usage pattern:
1. Use this pack for ecosystem orchestration (portfolio, backlog sync, multi-repo bundles).
2. Use Spec Kit-style spec/plan/tasks rigor inside each scoped implementation.
3. Keep organizational standards in knowledge modules, not hard-coded prompts.

## AIDLC Workflow Alignment (awslabs/aidlc-workflows)

This pack now incorporates the strongest AIDLC patterns in a tool-agnostic way:
- adaptive three-phase delivery (`inception -> construction -> operations`)
- opt-in extension model with blocking constraints
- human approval checkpoints and generated artifacts for each stage

### Adaptive Stage Selection

```bash
make plan-adaptive-workflow
```

Inputs:
- `project-template/workflow/request-profile.json`

Output:
- `project-template/workflow/selected-stages.json`

### Extension Resolution (Opt-In + Always-Enforced)

```bash
make resolve-extensions
```

Inputs:
- `project-template/extensions/extensions-catalog.json`
- `project-template/extensions/extension-selections.json`

Output:
- `project-template/extensions/resolved-extensions.json`

This mirrors AIDLC extension behavior while keeping your SDLC project-agnostic and reusable across ecosystems.

## Lightweight Lane for Ops/Fixes

For scoped investigations and fixes that do not justify full SDLC overhead, use the lite lane:

`triage -> investigate -> patch -> verify -> optional spec delta`

### Decide Full vs Lite

```bash
make select-workflow-lane
```

Input:
- `project-template/workflow/request-profile.json`

Output:
- `project-template/workflow/selected-lane.json`

Default full-lane triggers:
- new product/domain
- high complexity or risk
- migration work
- multi-repo work with high complexity/risk

### Lite Artifacts

- `project-template/lite/investigation.json`
- `project-template/lite/fix.json`
- `project-template/lite/github-issue.md`

Generate issue draft from lite artifacts:

```bash
make render-lite-issue
```

### Spec Delta Policy for Lite Work

Even in lite mode, update specs when any of these are true:
- behavioral contract changed
- NFR/security/performance requirements changed
- user-visible behavior changed

## Research Notes: Spec Kit + AIDLC Patterns Applied

Patterns included from upstream projects:
- adaptive workflow selection based on risk/scope (AIDLC)
- extension opt-in with blocking constraints (AIDLC)
- spec/process customization via externalized modules/presets (Spec Kit)
- workflow resumability and explicit gate checkpoints (Spec Kit)
