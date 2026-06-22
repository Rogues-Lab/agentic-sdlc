#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

PASS = "PASS"
FAIL = "FAIL"


def run_check(check):
    proc = subprocess.run(check["command"], shell=True, text=True, capture_output=True)
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    ok = True

    if proc.returncode != check.get("expected_exit_code", 0):
        ok = False

    for s in check.get("must_contain", []):
        if s not in output:
            ok = False

    for s in check.get("must_not_contain", []):
        if s and s in output:
            ok = False

    return {
        "id": check["id"],
        "test_id": check.get("test_id"),
        "type": check.get("type"),
        "status": PASS if ok else FAIL,
        "exit_code": proc.returncode,
        "expected_exit_code": check.get("expected_exit_code", 0),
        "command": check["command"],
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    out_path = Path(args.out)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = manifest.get("checks", [])
    results = [run_check(c) for c in checks]

    failed = [r for r in results if r["status"] == FAIL]
    gates = dict(manifest.get("gates", {}))
    gates["test_ready"] = PASS if not failed else FAIL

    payload = {
        "feature_id": manifest.get("feature_id"),
        "results": results,
        "summary": {
            "total": len(results),
            "passed": len(results) - len(failed),
            "failed": len(failed),
        },
        "gates": gates,
        "ship_policy": manifest.get("ship_policy", {}),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"VERIFICATION_RESULTS={out_path}")
    print(f"TOTAL={payload['summary']['total']}")
    print(f"PASSED={payload['summary']['passed']}")
    print(f"FAILED={payload['summary']['failed']}")

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
