#!/usr/bin/env bash
# Regression tests for the ship-gate evaluator.
# Each case asserts the gate's decision for a crafted set of artifacts.
# Run: bash tests/test_ship_gate.sh   (or: make test-gate)
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GATE="$ROOT/scripts/evaluate_ship_gate.py"
POLICY="$ROOT/project-template/policies/gate-policy.json"
PT="$ROOT/project-template"
FX="$ROOT/tests/fixtures"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS_COUNT=0
FAIL_COUNT=0

# assert_decision <name> <expected APPROVE|BLOCKED> <verification> <review> <qa>
assert_decision() {
  local name="$1" expected="$2" verif="$3" review="$4" qa="$5"
  local out
  out="$(python3 "$GATE" \
    --policy "$POLICY" \
    --verification-results "$verif" \
    --review-report "$review" \
    --qa-report "$qa" \
    --out "$TMP/ship.json" 2>&1)"
  local got
  got="$(python3 -c "import json;print(json.load(open('$TMP/ship.json'))['decision'])" 2>/dev/null)"
  if [ "$got" = "$expected" ]; then
    echo "PASS  $name (decision=$got)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL  $name -> expected=$expected got=$got"
    echo "$out" | sed 's/^/        /'
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

V_OK="$PT/reports/verification-results.json"
R_OK="$PT/reports/review-report.json"
Q_OK="$PT/reports/qa-report.json"

# Baseline happy path still approves.
assert_decision "happy-path approves" APPROVE "$V_OK" "$R_OK" "$Q_OK"

# #1 A rejected review must block even with no open critical/high findings.
assert_decision "rejected review blocks" BLOCKED "$V_OK" "$FX/review-rejected.json" "$Q_OK"

# #3 A QA defect marked 'fixed' must NOT block.
assert_decision "fixed defect does not block" APPROVE "$V_OK" "$R_OK" "$FX/qa-defect-fixed.json"

# #3 control: an open defect of the same severity still blocks.
assert_decision "open defect blocks" BLOCKED "$V_OK" "$R_OK" "$FX/qa-defect-open.json"

# #4 A valid, unexpired waiver un-blocks a failed required gate.
assert_decision "valid waiver unblocks gate" APPROVE "$FX/verification-test-failed.json" "$R_OK" "$Q_OK"

# #4 control: an expired waiver does NOT un-block.
assert_decision "expired waiver is ignored" BLOCKED "$FX/verification-expired-waiver.json" "$R_OK" "$Q_OK"

# Positive control: a failed security check blocks.
assert_decision "failed security check blocks" BLOCKED "$FX/verification-security-failed.json" "$R_OK" "$Q_OK"

# Identity cross-check: mismatched spec ids across artifacts block.
assert_decision "artifact identity mismatch blocks" BLOCKED "$V_OK" "$FX/review-wrong-spec.json" "$Q_OK"

echo "----------------------------------------"
echo "ship-gate tests: $PASS_COUNT passed, $FAIL_COUNT failed"
[ "$FAIL_COUNT" -eq 0 ]
