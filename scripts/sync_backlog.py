#!/usr/bin/env python3
import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


def _extract(obj, parts):
    if not parts:
        return obj
    head = parts[0]

    if head.endswith("[]"):
        key = head[:-2]
        arr = obj.get(key, []) if isinstance(obj, dict) else []
        if not isinstance(arr, list):
            return []
        tail = parts[1:]
        if not tail:
            return arr
        out = []
        for item in arr:
            val = _extract(item, tail)
            if isinstance(val, list):
                out.extend(val)
            elif val is not None:
                out.append(val)
        return out

    if not isinstance(obj, dict):
        return None
    return _extract(obj.get(head), parts[1:])


def get_by_path(obj, path):
    if path is None:
        return None
    if isinstance(path, str) and path.startswith("="):
        return path[1:]
    return _extract(obj, str(path).split("."))


def map_item(item, mapping):
    mapped = {}
    for out_field, in_path in mapping.items():
        mapped[out_field] = get_by_path(item, in_path)
    return mapped


def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def default_priority_inputs():
    return {
        "business_value": 5,
        "time_criticality": 5,
        "risk_reduction_or_opportunity": 5,
        "job_size": 5,
    }


def normalize_status(raw):
    if not raw:
        return "todo"
    s = str(raw).lower()
    if s in {"open", "todo", "backlog", "to do"}:
        return "todo"
    if s in {"in progress", "doing", "active", "in_progress"}:
        return "in_progress"
    if s in {"done", "closed", "resolved"}:
        return "done"
    if s in {"blocked"}:
        return "blocked"
    return "todo"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--external-items", required=True)
    ap.add_argument("--mapping", required=True)
    ap.add_argument("--backlog", required=True)
    args = ap.parse_args()

    ext_items = json.loads(Path(args.external_items).read_text(encoding="utf-8"))
    mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    backlog_path = Path(args.backlog)

    if backlog_path.exists():
        backlog = json.loads(backlog_path.read_text(encoding="utf-8"))
    else:
        backlog = {"project": "default", "items": []}

    items = backlog.setdefault("items", [])

    index = {}
    for i, item in enumerate(items):
        src = item.get("source", {})
        index[(src.get("system"), src.get("scope"), str(src.get("external_id")))] = i

    upserted = 0
    created = 0

    for ext in ext_items:
        mapped = map_item(ext, mapping)
        scope = mapped.get("scope")
        key = (mapped.get("system"), scope, str(mapped.get("id")))

        labels = mapped.get("labels")
        if not isinstance(labels, list):
            labels = []
        labels = [str(x) for x in labels if x is not None]

        base = {
            "id": f"BLG-{len(items) + 1:03d}",
            "title": mapped.get("title") or "Untitled",
            "description": mapped.get("description") or "",
            "source": {
                "system": mapped.get("system"),
                "scope": scope,
                "external_id": str(mapped.get("id")),
            },
            "status": normalize_status(mapped.get("status")),
            "type": "feature",
            "owner": mapped.get("owner") or "cto",
            "labels": labels,
            "risk_level": "medium",
            "effort_points": 5,
            "priority_inputs": default_priority_inputs(),
            "dependencies": [],
            "linked_spec_id": None,
            "linked_ticket_ids": [],
            "created_at": mapped.get("created_at") or now_iso(),
            "updated_at": mapped.get("updated_at") or now_iso(),
        }

        if key in index:
            existing = deepcopy(items[index[key]])
            existing["title"] = base["title"]
            existing["description"] = base["description"]
            existing["status"] = base["status"]
            existing["owner"] = base["owner"]
            existing["labels"] = base["labels"]
            existing["updated_at"] = base["updated_at"]
            existing["source"] = base["source"]
            items[index[key]] = existing
        else:
            items.append(base)
            index[key] = len(items) - 1
            created += 1

        upserted += 1

    backlog_path.parent.mkdir(parents=True, exist_ok=True)
    backlog_path.write_text(json.dumps(backlog, indent=2), encoding="utf-8")

    print(f"BACKLOG_SYNC_UPSERTED={upserted}")
    print(f"BACKLOG_SYNC_CREATED={created}")
    print(f"BACKLOG_PATH={backlog_path}")


if __name__ == "__main__":
    main()
