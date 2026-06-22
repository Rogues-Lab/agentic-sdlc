# External Adapter Sync Layer

This layer converts external work items (GitHub issues, Jira tickets, Linear issues) into canonical backlog items used by CTO scheduling and agentic SDLC execution.

## Canonical Flow

1. Pull external items into JSON.
2. Map fields using `mappings/*.mapping.json`.
3. Sync into canonical backlog with `scripts/sync_backlog.py`.
4. Score and rank with `scripts/schedule_backlog.py`.
5. CTO consumes ranked backlog to plan specs/tickets and delegation order.

## Visibility Model

- Product/user-facing requests are tracked in external systems.
- Canonical backlog tracks normalized status, priority inputs, and SDLC links (`SPEC-*`, `TKT-*`).
- Sync updates preserve source references (`system`, `external_id`) for traceability.


## Portfolio Enrichment

After sync, run portfolio enrichment to attach each backlog item to a `major_project_id` using repository mappings.
This allows CTO scheduling and reporting at ecosystem level (project, repo, item).


## Change Bundle Awareness

Backlog items may map to `change_bundle_ids` so CTO can plan discrete and multi-repo changes with explicit deployment impact and release sequencing.


## Knowledge Injection

Adapter outputs feed into change planning; project/repo standards are injected dynamically from the knowledge module registry during planning and delegation.
