# Feature Skeleton Example

- SPEC-login-hardening
- REQ-001: enforce session idle timeout
- AC-001: Given authenticated session idle > 30 min, when request arrives, then user is forced re-auth
- TEST-001 maps AC-001 via integration test command
- TKT-001 owns `auth/session.ts`, allowed `auth/middleware.ts`, non-owned `billing/*`
- RVW-001 recorded, no high findings
- QA-001 recorded, QA_READY=PASS
