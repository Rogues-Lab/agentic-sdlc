# TEST PLAN: <Feature Name>

## Metadata
- Test Plan ID: TSTPLAN-<id>
- Spec ID: SPEC-<id>

## Environment Matrix
| Env | Purpose | Command Prefix | Notes |
|---|---|---|---|
| local | dev verification | <cmd> | |
| ci | gate verification | <cmd> | |

## Test Inventory
| TEST ID | AC ID(s) | Type | Command | Expected |
|---|---|---|---|---|
| TEST-001 | AC-001 | unit | <command> | exit 0 |
| TEST-002 | AC-002 | integration | <command> | exit 0 + expected output |

## Negative/Edge Cases
- TEST-NEG-001:
- TEST-EDGE-001:

## Non-functional Checks
- Security:
- Performance:
- Reliability:

## Pass/Fail Policy
- Required pass tests:
- Allowed waivers (with expiry):
