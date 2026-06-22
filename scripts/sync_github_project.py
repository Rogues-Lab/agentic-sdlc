#!/usr/bin/env python3
import argparse
import subprocess
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-export", required=True, help="JSON export of GitHub Project items")
    ap.add_argument("--backlog", required=True)
    ap.add_argument(
        "--mapping",
        default=str(Path(__file__).resolve().parent.parent / "mappings" / "github-project-item.mapping.json"),
    )
    args = ap.parse_args()

    cmd = [
        "python3",
        str(Path(__file__).resolve().parent / "sync_backlog.py"),
        "--external-items",
        args.project_export,
        "--mapping",
        args.mapping,
        "--backlog",
        args.backlog,
    ]

    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
