# [ops] Prod API auth retries causing latency spikes (ISSUE-1001)

## Context
- Category: operations-support
- Repos: film-fun/community
- Deployments: community-web-prod

## Investigation Summary
- p95 latency increased by 40%
- 401 spikes around token-refresh windows
- Root cause: Retry storm from optimistic token refresh under contention

## Proposed Fix (Lite Lane)
- Summary: Token-refresh jitter and lock patch
- Strategy: Add jitter and lock-token refresh section
- Rollback: Disable new token-refresh path and revert lock logic

## Verification
- CHECK-auth-regression
- CHECK-latency-baseline

## Spec Delta
- Required: yes
- Notes: Clarify token-refresh retry policy and contention handling
