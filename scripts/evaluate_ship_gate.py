#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"

# Gates sourced authoritatively from their own report artifact rather than the
# verification manifest's self-asserted copy. Any gate not listed here falls back
# to verification-results `gates` (which for design_ready/build_ready is an
# externally-asserted input — see resolve_gate_value docstring).
AUTHORITATIVE_GATES = {"review_ready", "qa_ready"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def has_open_findings_with_severity(review, blocked_severities):
    for f in review.get("findings", []):
        if f.get("status") == "open" and f.get("severity") in blocked_severities:
            return True
    return False


def has_open_defects_with_severity(qa, blocked_severities):
    # Only unresolved defects block. A defect marked "fixed"/"resolved"/"closed"
    # has been remediated and must not block the ship gate.
    blocking_statuses = {"open", "reopened"}
    for d in qa.get("defects", []):
        if d.get("status") in blocking_statuses and d.get("severity") in blocked_severities:
            return True
    return False


def resolve_gate_value(gate, verification, review, qa):
    """Return the authoritative PASS/FAIL value for a required gate.

    - review_ready: derived from the review report's own `decision` and
      `gates.review_ready` — NOT the manifest's self-asserted copy. A review whose
      decision is anything other than APPROVE fails the gate.
    - qa_ready: derived from the QA report's `gates.qa_ready`.
    - everything else (design_ready, build_ready, test_ready): read from
      verification-results. `test_ready` is computed by run_verification.py;
      `design_ready`/`build_ready` are externally-asserted inputs supplied in the
      verification manifest (the pack does not currently compute them).
    """
    if gate == "review_ready":
        decision = str(review.get("decision", "")).upper()
        if decision and decision != "APPROVE":
            return FAIL
        return review.get("gates", {}).get(
            "review_ready", verification.get("gates", {}).get(gate)
        )
    if gate == "qa_ready":
        return qa.get("gates", {}).get(
            "qa_ready", verification.get("gates", {}).get(gate)
        )
    return verification.get("gates", {}).get(gate)


def parse_dt(value):
    if not value:
        return None
    try:
        text = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def waiver_is_valid(waiver, required_fields, max_duration_days, now):
    """Validate a waiver. Returns (is_valid, invalid_reason)."""
    for field in required_fields:
        if not str(waiver.get(field, "")).strip():
            return False, f"missing required field '{field}'"

    expires = parse_dt(waiver.get("expires_at"))
    if expires is None:
        return False, "invalid or missing expires_at"
    if expires < now:
        return False, "expired"

    if max_duration_days:
        created = parse_dt(waiver.get("created_at"))
        if created is not None and (expires - created).days > max_duration_days:
            return False, f"duration exceeds max_duration_days ({max_duration_days})"

    return True, None


def waiver_matches(waiver, reason):
    """A waiver matches a blocking reason by explicit code or by typed target."""
    code = reason["code"]
    if waiver.get("code") and waiver["code"] == code:
        return True
    if waiver.get("target") and waiver["target"] == code:
        return True
    if waiver.get("gate") and code == f"gate:{waiver['gate']}":
        return True
    if waiver.get("check_id") and code == f"check:{waiver['check_id']}":
        return True
    if waiver.get("check_type") and reason.get("check_type") == waiver["check_type"]:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", required=True)
    ap.add_argument("--verification-results", required=True)
    ap.add_argument("--review-report", required=True)
    ap.add_argument("--qa-report", required=True)
    ap.add_argument("--decision-context", required=False)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    policy = load(args.policy)
    verification = load(args.verification_results)
    review = load(args.review_report)
    qa = load(args.qa_report)

    decision_context = {}
    if args.decision_context and Path(args.decision_context).exists():
        dc = load(args.decision_context)
        decision_context = dc.get("decision_context", dc)

    quality = decision_context.get("quality_gates", {}) if isinstance(decision_context, dict) else {}

    required_gates = quality.get("required_gates", policy.get("required_gates", []))
    blocked_review_severities = set(quality.get("blocked_on_review_severity", ["critical", "high"]))
    blocked_qa_severities = set(quality.get("blocked_on_qa_severity", ["critical", "high"]))

    blocked_types = set(
        quality.get(
            "block_on_failed_types",
            verification.get("ship_policy", {}).get("block_on_failed_types", []),
        )
    )

    # Each reason carries a stable `code` so waivers can target it precisely and
    # duplicates (from required-gate loop vs belt-and-suspenders checks) collapse.
    reasons = []

    def add_reason(code, message, **extra):
        entry = {"code": code, "message": message}
        entry.update(extra)
        reasons.append(entry)

    # Feature-identity cross-check: refuse to ship if the three artifacts do not
    # describe the same spec/feature (prevents verifying feature A, shipping B).
    identities = {
        verification.get("feature_id"),
        review.get("spec_id"),
        qa.get("spec_id"),
    }
    identities.discard(None)
    if len(identities) > 1:
        add_reason(
            "identity_mismatch",
            f"Artifact identity mismatch across reports: {sorted(identities)}",
        )

    for gate in required_gates:
        value = resolve_gate_value(gate, verification, review, qa)
        if value != PASS:
            add_reason(f"gate:{gate}", f"Gate not PASS: {gate}={value}")

    for r in verification.get("results", []):
        if r.get("status") == FAIL and r.get("type") in blocked_types:
            add_reason(
                f"check:{r.get('id')}",
                f"Failed blocked check type: {r.get('id')} ({r.get('type')})",
                check_type=r.get("type"),
            )

    if has_open_findings_with_severity(review, blocked_review_severities):
        add_reason(
            "review_findings",
            f"Open review findings in severities: {','.join(sorted(blocked_review_severities))}",
        )

    if has_open_defects_with_severity(qa, blocked_qa_severities):
        add_reason(
            "qa_defects",
            f"Open QA defects in severities: {','.join(sorted(blocked_qa_severities))}",
        )

    # Belt-and-suspenders: enforce the review verdict and QA gate even if a policy
    # omits review_ready/qa_ready from required_gates. Same codes -> deduped below.
    review_decision = str(review.get("decision", "")).upper()
    if review_decision and review_decision != "APPROVE":
        add_reason("gate:review_ready", f"Review not approved: decision={review_decision}")

    qa_gate = qa.get("gates", {}).get("qa_ready")
    if qa_gate != PASS:
        add_reason("gate:qa_ready", f"QA gate not PASS: qa_ready={qa_gate}")

    # Dedupe by code, preserving first occurrence.
    seen_codes = set()
    deduped = []
    for reason in reasons:
        if reason["code"] in seen_codes:
            continue
        seen_codes.add(reason["code"])
        deduped.append(reason)
    reasons = deduped

    # Apply waivers (deliberate, time-boxed risk acceptance). Only honored when the
    # policy enables them and each waiver carries the required fields and is unexpired.
    waiver_policy = policy.get("waiver_policy", {})
    waivers_enabled = bool(waiver_policy.get("allowed", False))
    required_waiver_fields = waiver_policy.get(
        "required_fields", ["id", "rationale", "approver", "expires_at"]
    )
    max_duration_days = waiver_policy.get("max_duration_days")
    now = datetime.now(timezone.utc)

    valid_waivers = []
    invalid_waivers = []
    if waivers_enabled:
        for w in verification.get("waivers", []):
            ok, why = waiver_is_valid(w, required_waiver_fields, max_duration_days, now)
            if ok:
                valid_waivers.append(w)
            else:
                invalid_waivers.append({"id": w.get("id"), "reason": why})

    active_reasons = []
    waived = []
    for reason in reasons:
        matched = next((w for w in valid_waivers if waiver_matches(w, reason)), None)
        if matched:
            waived.append(
                {
                    "code": reason["code"],
                    "message": reason["message"],
                    "waiver_id": matched.get("id"),
                    "approver": matched.get("approver"),
                    "expires_at": matched.get("expires_at"),
                }
            )
        else:
            active_reasons.append(reason)

    decision = "APPROVE" if not active_reasons else BLOCKED

    out = {
        "decision": decision,
        "status": PASS if decision == "APPROVE" else FAIL,
        "resolved_policy": {
            "required_gates": required_gates,
            "blocked_review_severities": sorted(blocked_review_severities),
            "blocked_qa_severities": sorted(blocked_qa_severities),
            "blocked_check_types": sorted(blocked_types),
            "waivers_enabled": waivers_enabled,
        },
        "reasons": [r["message"] for r in active_reasons],
        "waived": waived,
        "invalid_waivers": invalid_waivers,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"SHIP_DECISION={decision}")
    for reason in active_reasons:
        print(f"- {reason['message']}")
    for w in waived:
        print(f"~ WAIVED [{w['waiver_id']}]: {w['message']}")
    for iw in invalid_waivers:
        print(f"! IGNORED WAIVER [{iw['id']}]: {iw['reason']}")

    if decision != "APPROVE":
        sys.exit(1)


if __name__ == "__main__":
    main()
