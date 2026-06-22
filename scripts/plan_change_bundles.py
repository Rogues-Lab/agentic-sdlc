#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def wsjf(inputs):
    bv = float(inputs.get("business_value", 0))
    tc = float(inputs.get("time_criticality", 0))
    rr = float(inputs.get("risk_reduction_or_opportunity", 0))
    js = float(inputs.get("job_size", 5))
    js = js if js > 0 else 5
    return (bv + tc + rr) / js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--change-bundles", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bundles = json.loads(Path(args.change_bundles).read_text(encoding="utf-8")).get("change_bundles", [])

    ranked = []
    for b in bundles:
        workstreams = b.get("workstreams", [])
        deployments = sorted({d for ws in workstreams for d in ws.get("deployments_impacted", [])})
        repos = sorted({ws.get("repo") for ws in workstreams if ws.get("repo")})
        ranked.append({
            "id": b.get("id"),
            "title": b.get("title"),
            "major_project_id": b.get("major_project_id"),
            "status": b.get("status"),
            "score": round(wsjf(b.get("priority_inputs", {})), 4),
            "repos": repos,
            "deployments_impacted": deployments,
            "workstream_count": len(workstreams),
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)

    out = {"ranked_change_bundles": ranked}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"CHANGE_BUNDLES={len(ranked)}")
    if ranked:
        print(f"TOP_CHANGE_BUNDLE={ranked[0]['id']}:{ranked[0]['score']}")
    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
