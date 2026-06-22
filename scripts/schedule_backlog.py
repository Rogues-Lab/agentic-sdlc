#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


BLOCKED_PENALTY_DEFAULT = 1000


def wsjf(inputs, weights, default_job_size=5):
    bv = float(inputs.get("business_value", 0)) * float(weights.get("business_value", 1.0))
    tc = float(inputs.get("time_criticality", 0)) * float(weights.get("time_criticality", 1.0))
    rr = float(inputs.get("risk_reduction_or_opportunity", 0)) * float(weights.get("risk_reduction_or_opportunity", 1.0))
    js = float(inputs.get("job_size", default_job_size))
    js = js if js > 0 else default_job_size
    return (bv + tc + rr) / js


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backlog", required=True)
    ap.add_argument("--policy", required=True)
    ap.add_argument("--decision-context", required=False)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    backlog = json.loads(Path(args.backlog).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))

    decision_context = {}
    if args.decision_context and Path(args.decision_context).exists():
        dc = json.loads(Path(args.decision_context).read_text(encoding="utf-8"))
        decision_context = dc.get("decision_context", dc)

    priority_overrides = decision_context.get("priority", {}) if isinstance(decision_context, dict) else {}

    weights = dict(policy.get("weights", {}))
    weights.update(priority_overrides.get("weights", {}))

    blocked_penalty = int(priority_overrides.get("blocked_penalty", policy.get("blocked_penalty", BLOCKED_PENALTY_DEFAULT)))
    default_job_size = int(priority_overrides.get("default_job_size", policy.get("default_job_size", 5)))

    ranked = []
    project_scores = {}
    repo_scores = {}

    for item in backlog.get("items", []):
        inputs = item.get("priority_inputs", {})
        score = wsjf(inputs, weights, default_job_size)
        if item.get("status") == "blocked":
            score -= blocked_penalty

        entry = {
            "id": item.get("id"),
            "title": item.get("title"),
            "status": item.get("status"),
            "score": round(score, 4),
            "source": item.get("source", {}),
            "major_project_id": item.get("major_project_id", "unassigned"),
            "repo": item.get("repo") or item.get("source", {}).get("scope"),
            "linked_spec_id": item.get("linked_spec_id"),
        }
        ranked.append(entry)

        mp = entry["major_project_id"]
        project_scores[mp] = project_scores.get(mp, 0.0) + score

        repo = entry.get("repo") or "unscoped"
        repo_scores[repo] = repo_scores.get(repo, 0.0) + score

    ranked.sort(key=lambda x: x["score"], reverse=True)

    ranked_projects = [
        {"major_project_id": k, "aggregate_score": round(v, 4)}
        for k, v in project_scores.items()
    ]
    ranked_projects.sort(key=lambda x: x["aggregate_score"], reverse=True)

    ranked_repos = [
        {"repo": k, "aggregate_score": round(v, 4)}
        for k, v in repo_scores.items()
    ]
    ranked_repos.sort(key=lambda x: x["aggregate_score"], reverse=True)

    out = {
        "method": policy.get("method", "wsjf"),
        "resolved_priority_policy": {
            "weights": weights,
            "default_job_size": default_job_size,
            "blocked_penalty": blocked_penalty,
        },
        "ranked_items": ranked,
        "ranked_major_projects": ranked_projects,
        "ranked_repos": ranked_repos,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"RANKED_BACKLOG_PATH={out_path}")
    print(f"ITEMS={len(ranked)}")
    if ranked:
        print(f"TOP_ITEM={ranked[0]['id']}:{ranked[0]['score']}")
    if ranked_projects:
        top = ranked_projects[0]
        print(f"TOP_MAJOR_PROJECT={top['major_project_id']}:{top['aggregate_score']}")


if __name__ == "__main__":
    main()
