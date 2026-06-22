#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backlog", required=True)
    ap.add_argument("--portfolio", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    backlog = json.loads(Path(args.backlog).read_text(encoding="utf-8"))
    portfolio = json.loads(Path(args.portfolio).read_text(encoding="utf-8"))

    repo_to_project = {}
    for p in portfolio.get("major_projects", []):
        for repo in p.get("repos", []):
            repo_to_project[repo] = p.get("id")

    enriched = 0
    for item in backlog.get("items", []):
        scope = item.get("source", {}).get("scope")
        project_id = repo_to_project.get(scope)
        if project_id:
            item["major_project_id"] = project_id
            item["repo"] = scope
            enriched += 1
        else:
            item.setdefault("major_project_id", "unassigned")
            if scope:
                item.setdefault("repo", scope)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(backlog, indent=2), encoding="utf-8")

    print(f"ENRICHED_ITEMS={enriched}")
    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
