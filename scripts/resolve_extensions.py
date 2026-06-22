#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--selections", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    catalog = load_json(args.catalog)
    selections = load_json(args.selections)

    enabled = []
    disabled = []
    blocking_rules = []

    for ext in catalog.get("extensions", []):
        always = bool(ext.get("always_enforced", False))
        opt_in_key = ext.get("opt_in_key")
        selected = bool(selections.get(opt_in_key, False)) if opt_in_key else False
        is_enabled = always or selected

        if is_enabled:
            enabled.append(
                {
                    "id": ext.get("id"),
                    "title": ext.get("title"),
                    "blocking": bool(ext.get("blocking", True)),
                    "rules": ext.get("rules", []),
                }
            )
            if bool(ext.get("blocking", True)):
                for rule in ext.get("rules", []):
                    blocking_rules.append(
                        {
                            "extension_id": ext.get("id"),
                            "rule_id": rule.get("id"),
                            "description": rule.get("description"),
                        }
                    )
        else:
            disabled.append({"id": ext.get("id"), "title": ext.get("title")})

    out = {
        "enabled_extensions": enabled,
        "disabled_extensions": disabled,
        "blocking_rules": blocking_rules,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(f"EXTENSIONS_ENABLED={len(enabled)}")
    print(f"BLOCKING_RULES={len(blocking_rules)}")
    print(f"OUT={out_path}")


if __name__ == "__main__":
    main()
