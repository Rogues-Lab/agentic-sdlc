Goal: <business/technical outcome>
Spec: SPEC-<id>
Ticket: TKT-<id>
Implementation Agent:
- preferred: auto|codex|claude
- allowed: ["codex", "claude"]
- mode: run|session
- fallback: <codex or claude>
Execution Channel:
- channel: acp_subscription
- hook_profile: default-coding-lifecycle
- direct_model_execution: disallowed
Scope:
- Owned files: ...
- Allowed files: ...
- Non-owned files: ...
Constraints:
- compatibility: ...
- security: ...
- performance: ...
Acceptance Criteria:
- AC-001: ...
- AC-002: ...
Tests Required:
- TEST-001 maps AC-001
- TEST-002 maps AC-002
Verification:
- Run commands from verification manifest and report outputs
Deliverables:
- code changes
- commands run + results
- unresolved risks
- hook events emitted
