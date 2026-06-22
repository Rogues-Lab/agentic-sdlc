#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--request-profile", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    p = load_json(args.request_profile)

    complexity = int(p.get("complexity_score", 0))
    risk = int(p.get("risk_score", 0))
    new_domain = bool(p.get("new_product_or_major_domain", False))
    multi_repo = bool(p.get("multi_repo_or_bundle", False))
    requires_migration = bool(p.get("requires_migration", False))
    ops_impact = bool(p.get("operations_impact", False))

    full_reasons = []
    if new_domain:
        full_reasons.append("new_product_or_major_domain=true")
    if complexity >= 7:
        full_reasons.append("complexity_score>=7")
    if risk >= 7:
        full_reasons.append("risk_score>=7")
    if multi_repo and (complexity >= 6 or risk >= 6):
        full_reasons.append("multi_repo_or_bundle with high complexity/risk")
    if requires_migration:
        full_reasons.append("requires_migration=true")

    lane = "full" if full_reasons else "lite"

    required_artifacts = [
        "investigation.json",
        "fix.json",
        "verification-results.json",
    ]
    if lane == "full":
        required_artifacts.extend(["spec.json", "test-plan.json", "tickets.json"])
    else:
        required_artifacts.append("spec-delta-note(optional)")

    out = {
        "request_id": p.get("request_id"),
        "selected_lane": lane,
        "lane_reasons": full_reasons if full_reasons else ["low-to-medium risk scoped change"],
        "ops_impact": ops_impact,
        "required_artifacts": required_artifacts,
        "policy": {
            "spec_update_required_if": [
                "behavioral contract changed",
                "nfr/performance/security requirements changed",
                "user-visible behavior changed",
            ]
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"WORKFLOW_LANE={lane}")
    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
