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

    profile = load_json(args.request_profile)

    complexity = int(profile.get("complexity_score", 0))
    risk = int(profile.get("risk_score", 0))
    new_domain = bool(profile.get("new_product_or_major_domain", False))
    ops_impact = bool(profile.get("operations_impact", False))
    migration = bool(profile.get("requires_migration", False))
    multi_repo = bool(profile.get("multi_repo_or_bundle", False))

    stages = []
    reasons = []

    inception_needed = new_domain or complexity >= 4 or risk >= 4 or multi_repo
    if inception_needed:
        stages.append("inception")
        reasons.append("Inception required due to complexity/risk/new-domain/multi-repo scope")

    construction_needed = True
    if construction_needed:
        stages.append("construction")
        reasons.append("Construction always required for implementation and verification")

    operations_needed = ops_impact or migration or risk >= 6
    if operations_needed:
        stages.append("operations")
        reasons.append("Operations required due to deployment risk/impact or migration")

    out = {
        "request_id": profile.get("request_id"),
        "selected_stages": stages,
        "stage_reasons": reasons,
        "input_profile": profile,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"WORKFLOW_STAGES={','.join(stages)}")
    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
