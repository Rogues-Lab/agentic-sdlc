#!/usr/bin/env python3
import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any, Dict, List, Set


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_repos_from_changes(change_bundles: Dict[str, Any]) -> Set[str]:
    repos = set()
    for bundle in change_bundles.get("change_bundles", []):
        for ws in bundle.get("workstreams", []):
            repo = ws.get("repo")
            if repo:
                repos.add(repo)
    return repos


def collect_deployments_from_changes(change_bundles: Dict[str, Any]) -> Set[str]:
    deployments = set()
    for bundle in change_bundles.get("change_bundles", []):
        for ws in bundle.get("workstreams", []):
            for dep in ws.get("deployments_impacted", []):
                if dep:
                    deployments.add(dep)
    return deployments


def collect_change_bundle_ids(change_bundles: Dict[str, Any]) -> Set[str]:
    return {b.get("id") for b in change_bundles.get("change_bundles", []) if b.get("id")}


def deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in incoming.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def any_match(values: Set[str], expected: List[str]) -> bool:
    if not expected:
        return True
    return any(v in values for v in expected)


def any_prefix_match(values: Set[str], prefixes: List[str]) -> bool:
    if not prefixes:
        return True
    return any(any(v.startswith(p) for p in prefixes) for v in values)


def any_glob_match(values: Set[str], patterns: List[str]) -> bool:
    if not patterns:
        return True
    return any(any(fnmatch.fnmatch(v, pat) for pat in patterns) for v in values)


def matches_rule(rule: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    match = rule.get("match", {})
    if match.get("always"):
        return True

    if not any_match({ctx.get("major_project_id")} - {None}, match.get("major_project_ids", [])):
        return False
    if not any_match({ctx.get("product_id")} - {None}, match.get("product_ids", [])):
        return False
    if not any_match(set(ctx.get("repos", [])), match.get("repos", [])):
        return False
    if not any_prefix_match(set(ctx.get("repos", [])), match.get("repo_prefixes", [])):
        return False
    if not any_glob_match(set(ctx.get("repos", [])), match.get("repo_patterns", [])):
        return False
    if not any_match(set(ctx.get("deployments", [])), match.get("deployment_targets", [])):
        return False
    if not any_match(set(ctx.get("change_bundle_ids", [])), match.get("change_bundle_ids", [])):
        return False
    if not any_match(set(ctx.get("tags", [])), match.get("tags", [])):
        return False

    return True


def resolve_modules_from_rules(
    registry: Dict[str, Any], ctx: Dict[str, Any]
) -> Dict[str, Any]:
    module_library = {m["id"]: m for m in registry.get("module_library", [])}
    rules = registry.get("resolver_rules", [])
    sorted_rules = sorted(rules, key=lambda r: (r.get("priority", 1000), r.get("id", "")))

    modules: List[Dict[str, Any]] = []
    applied_rules: List[Dict[str, Any]] = []
    decision_context: Dict[str, Any] = {}

    for rule in sorted_rules:
        if not matches_rule(rule, ctx):
            continue

        applied_rules.append({"id": rule.get("id"), "priority": rule.get("priority", 1000)})

        for mid in rule.get("module_ids", []):
            if mid in module_library:
                modules.append(module_library[mid])

        for m in rule.get("modules", []):
            modules.append(m)

        if isinstance(rule.get("decision_overrides"), dict):
            decision_context = deep_merge(decision_context, rule["decision_overrides"])

    dedup = {}
    for m in modules:
        dedup[m["id"]] = m

    return {
        "modules": list(dedup.values()),
        "applied_rules": applied_rules,
        "decision_context": decision_context,
    }


def resolve_modules_legacy(registry: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    modules: List[Dict[str, Any]] = []

    for m in registry.get("default_modules", []):
        modules.append(m)

    major_project_id = ctx.get("major_project_id")
    if major_project_id:
        for m in registry.get("major_project_modules", {}).get(major_project_id, []):
            modules.append(m)

    for repo in sorted(set(ctx.get("repos", []))):
        for m in registry.get("repo_modules", {}).get(repo, []):
            modules.append(m)

    dedup = {}
    for m in modules:
        dedup[m["id"]] = m

    return {
        "modules": list(dedup.values()),
        "applied_rules": [{"id": "legacy-default-major-repo", "priority": 1000}],
        "decision_context": {},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--major-project-id", required=False)
    ap.add_argument("--product-id", required=False)
    ap.add_argument("--repos", default="", help="Comma-separated repo list")
    ap.add_argument("--tags", default="", help="Comma-separated resolver tags, e.g. hotfix,release")
    ap.add_argument("--change-bundles", required=False)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    registry_path = Path(args.registry)
    root = registry_path.parent.parent.parent
    registry = load_json(registry_path)

    repos = {r.strip() for r in args.repos.split(",") if r.strip()}
    deployments = set()
    change_bundle_ids = set()

    if args.change_bundles:
        cb = load_json(Path(args.change_bundles))
        repos |= collect_repos_from_changes(cb)
        deployments |= collect_deployments_from_changes(cb)
        change_bundle_ids |= collect_change_bundle_ids(cb)

    ctx = {
        "major_project_id": args.major_project_id,
        "product_id": args.product_id,
        "repos": sorted(repos),
        "deployments": sorted(deployments),
        "change_bundle_ids": sorted(change_bundle_ids),
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
    }

    if registry.get("resolver_rules"):
        resolved = resolve_modules_from_rules(registry, ctx)
    else:
        resolved = resolve_modules_legacy(registry, ctx)

    modules = resolved["modules"]
    loaded = []
    missing = []

    for m in modules:
        rel = Path(m["path"])
        p = rel if rel.is_absolute() else (root / rel)
        if p.exists():
            loaded.append(
                {
                    "id": m["id"],
                    "tags": m.get("tags", []),
                    "path": str(p),
                    "content": p.read_text(encoding="utf-8"),
                }
            )
        else:
            missing.append({"id": m["id"], "path": str(p)})

    out_json = {
        "selector_context": ctx,
        "applied_rules": resolved["applied_rules"],
        "decision_context": resolved["decision_context"],
        "loaded_modules": [
            {"id": x["id"], "tags": x["tags"], "path": x["path"]} for x in loaded
        ],
        "missing_modules": missing,
    }

    out_json_path = Path(args.out_json)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(out_json, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Injected Knowledge Context")
    lines.append("")
    lines.append(f"major_project_id: {args.major_project_id}")
    lines.append(f"product_id: {args.product_id or '(none)'}")
    lines.append(f"repos: {', '.join(sorted(repos)) if repos else '(none)'}")
    lines.append(f"deployments: {', '.join(sorted(deployments)) if deployments else '(none)'}")
    lines.append(f"change_bundle_ids: {', '.join(sorted(change_bundle_ids)) if change_bundle_ids else '(none)'}")
    lines.append(f"tags: {', '.join(ctx['tags']) if ctx['tags'] else '(none)'}")
    lines.append("")

    lines.append("## Applied Rules")
    for r in resolved["applied_rules"]:
        lines.append(f"- {r['id']} (priority={r['priority']})")
    lines.append("")

    lines.append("## Decision Context")
    lines.append("```json")
    lines.append(json.dumps(resolved["decision_context"], indent=2))
    lines.append("```")
    lines.append("")

    for mod in loaded:
        lines.append(f"## Module: {mod['id']}")
        lines.append(f"source: {mod['path']}")
        lines.append("")
        lines.append(mod["content"].strip())
        lines.append("")

    if missing:
        lines.append("## Missing Modules")
        for m in missing:
            lines.append(f"- {m['id']}: {m['path']}")

    out_md_path = Path(args.out_md)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"KB_MODULES_LOADED={len(loaded)}")
    print(f"KB_MODULES_MISSING={len(missing)}")
    print(f"KB_RULES_APPLIED={len(resolved['applied_rules'])}")
    print(f"OUT_JSON={out_json_path}")
    print(f"OUT_MD={out_md_path}")


if __name__ == "__main__":
    main()
