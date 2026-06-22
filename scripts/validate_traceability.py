#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path

ID_PATTERNS = {
    "spec": re.compile(r"^SPEC-[a-z0-9-]+$"),
    "req": re.compile(r"^REQ-[0-9]{3}$"),
    "ac": re.compile(r"^AC-[0-9]{3}$"),
    "tkt": re.compile(r"^TKT-[0-9]{3}$"),
    "test": re.compile(r"^TEST-[0-9]{3}$"),
    "check": re.compile(r"^CHECK-[0-9]{3}$"),
}


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to parse JSON at {path}: {exc}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--feature-dir", required=True, help="Directory with artifacts/*.json")
    args = p.parse_args()

    base = Path(args.feature_dir)
    spec = load_json(base / "artifacts" / "spec.json")
    tickets = load_json(base / "artifacts" / "tickets.json")
    test_plan = load_json(base / "artifacts" / "test-plan.json")
    manifest = load_json(base / "artifacts" / "verification-manifest.json")

    errors = []

    spec_id = spec.get("spec_id", "")
    if not ID_PATTERNS["spec"].match(spec_id):
        errors.append(f"Invalid spec_id: {spec_id}")

    req_ids = {r.get("id") for r in spec.get("requirements", [])}
    ac_ids = {a.get("id") for a in spec.get("acceptance_criteria", [])}

    for req_id in req_ids:
        if not ID_PATTERNS["req"].match(req_id or ""):
            errors.append(f"Invalid requirement id: {req_id}")

    req_to_acs = {req_id: [] for req_id in req_ids}

    for ac in spec.get("acceptance_criteria", []):
        ac_id = ac.get("id")
        if not ID_PATTERNS["ac"].match(ac_id or ""):
            errors.append(f"Invalid acceptance criterion id: {ac_id}")
        req_ref = ac.get("requirement_id")
        if req_ref not in req_ids:
            errors.append(f"AC {ac_id} references missing requirement {req_ref}")
        else:
            req_to_acs[req_ref].append(ac_id)
        for field in ("given", "when", "then"):
            if not str(ac.get(field, "")).strip():
                errors.append(f"AC {ac_id} missing {field}")

    for req_id, mapped_acs in req_to_acs.items():
        if not mapped_acs:
            errors.append(f"Requirement {req_id} has no acceptance criteria")

    for t in tickets.get("tickets", []):
        t_id = t.get("id")
        if not ID_PATTERNS["tkt"].match(t_id or ""):
            errors.append(f"Invalid ticket id: {t_id}")
        if t.get("spec_id") != spec_id:
            errors.append(f"Ticket {t_id} spec_id mismatch: {t.get('spec_id')} != {spec_id}")
        linked_ac = set(t.get("linked_ac_ids", []))
        missing = sorted(linked_ac - ac_ids)
        if missing:
            errors.append(f"Ticket {t_id} references missing AC IDs: {missing}")

    tests = test_plan.get("tests", [])
    test_ids = {t.get("id") for t in tests}
    ac_to_tests = {ac_id: [] for ac_id in ac_ids}

    for t in tests:
        test_id = t.get("id")
        if not ID_PATTERNS["test"].match(test_id or ""):
            errors.append(f"Invalid test id: {test_id}")
        if not str(t.get("command", "")).strip():
            errors.append(f"Test {test_id} missing command")
        for ac_id in t.get("ac_ids", []):
            if ac_id not in ac_ids:
                errors.append(f"Test {test_id} references missing AC ID: {ac_id}")
            else:
                ac_to_tests[ac_id].append(test_id)

    for ac_id, mapped_tests in ac_to_tests.items():
        if not mapped_tests:
            errors.append(f"AC {ac_id} has no mapped TEST")

    checks = manifest.get("checks", [])
    for c in checks:
        c_id = c.get("id")
        if not ID_PATTERNS["check"].match(c_id or ""):
            errors.append(f"Invalid check id: {c_id}")
        t_id = c.get("test_id")
        if t_id not in test_ids:
            errors.append(f"Check {c_id} references missing TEST ID: {t_id}")
        for ac_id in c.get("ac_ids", []):
            if ac_id not in ac_ids:
                errors.append(f"Check {c_id} references missing AC ID: {ac_id}")
        if not str(c.get("command", "")).strip():
            errors.append(f"Check {c_id} missing command")

    if errors:
        print("TRACEABILITY_VALIDATION=FAIL")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)

    print("TRACEABILITY_VALIDATION=PASS")
    print(f"spec_id={spec_id}")
    print(f"requirements={len(req_ids)}")
    print(f"acceptance_criteria={len(ac_ids)}")
    print(f"tickets={len(tickets.get('tickets', []))}")
    print(f"tests={len(tests)}")
    print(f"checks={len(checks)}")


if __name__ == "__main__":
    main()
