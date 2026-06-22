#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <target-dir>" >&2
  exit 2
fi

TARGET="$1"
PACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$TARGET/artifacts" "$TARGET/reports" "$TARGET/policies" "$TARGET/change-bundles" "$TARGET/knowledge" "$TARGET/portfolio"
cp "$PACK_DIR/project-template/artifacts/spec.json" "$TARGET/artifacts/spec.json"
cp "$PACK_DIR/project-template/artifacts/tickets.json" "$TARGET/artifacts/tickets.json"
cp "$PACK_DIR/project-template/artifacts/test-plan.json" "$TARGET/artifacts/test-plan.json"
cp "$PACK_DIR/project-template/artifacts/verification-manifest.json" "$TARGET/artifacts/verification-manifest.json"
cp "$PACK_DIR/project-template/reports/review-report.json" "$TARGET/reports/review-report.json"
cp "$PACK_DIR/project-template/reports/qa-report.json" "$TARGET/reports/qa-report.json"
cp "$PACK_DIR/project-template/policies/gate-policy.json" "$TARGET/policies/gate-policy.json"
cp "$PACK_DIR/project-template/change-bundles/change-bundles.json" "$TARGET/change-bundles/change-bundles.json"
cp "$PACK_DIR/project-template/portfolio/projects.json" "$TARGET/portfolio/projects.json"
cp "$PACK_DIR/project-template/knowledge/module-registry.json" "$TARGET/knowledge/module-registry.json"

echo "BOOTSTRAP_COMPLETE=$TARGET"
