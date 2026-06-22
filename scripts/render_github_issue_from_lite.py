#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def to_md_list(items):
    if not items:
        return "- (none)"
    return "\n".join([f"- {i}" for i in items])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--investigation", required=True)
    ap.add_argument("--fix", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    inv = load_json(args.investigation)
    fix = load_json(args.fix)

    repos = inv.get("suspected_scope", {}).get("repos", [])
    deployments = inv.get("suspected_scope", {}).get("deployments", [])

    lines = []
    lines.append(f"# [ops] {inv.get('title', 'Issue')} ({inv.get('issue_id', 'n/a')})")
    lines.append("")
    lines.append("## Context")
    lines.append(f"- Category: {inv.get('category', 'unspecified')}")
    lines.append(f"- Repos: {', '.join(repos) if repos else '(none)'}")
    lines.append(f"- Deployments: {', '.join(deployments) if deployments else '(none)'}")
    lines.append("")
    lines.append("## Investigation Summary")
    lines.append(to_md_list(inv.get("symptoms", [])))
    lines.append(f"- Root cause: {inv.get('root_cause', '(unknown)')}")
    lines.append("")
    lines.append("## Proposed Fix (Lite Lane)")
    lines.append(f"- Summary: {fix.get('summary', '(none)')}")
    lines.append(f"- Strategy: {inv.get('fix_strategy', '(none)')}")
    lines.append(f"- Rollback: {fix.get('rollback_plan', '(none)')}")
    lines.append("")
    lines.append("## Verification")
    lines.append(to_md_list(fix.get("checks_required", [])))
    lines.append("")
    lines.append("## Spec Delta")
    lines.append(f"- Required: {'yes' if fix.get('spec_delta_required', False) else 'no'}")
    lines.append(f"- Notes: {inv.get('spec_delta_notes', '(none)')}")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
