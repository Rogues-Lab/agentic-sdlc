FEATURE_DIR ?= project-template
MAJOR_PROJECT_ID ?= film-fun-ecosystem
PRODUCT_ID ?=
REPOS ?=
TAGS ?=


validate:
	python3 scripts/validate_traceability.py --feature-dir $(FEATURE_DIR)

verify:
	python3 scripts/run_verification.py --manifest $(FEATURE_DIR)/artifacts/verification-manifest.json --out $(FEATURE_DIR)/reports/verification-results.json

gate:
	python3 scripts/evaluate_ship_gate.py \
		--policy $(FEATURE_DIR)/policies/gate-policy.json \
		--verification-results $(FEATURE_DIR)/reports/verification-results.json \
		--review-report $(FEATURE_DIR)/reports/review-report.json \
		--qa-report $(FEATURE_DIR)/reports/qa-report.json \
		--out $(FEATURE_DIR)/reports/ship-decision.json

sync-backlog:
	python3 scripts/sync_backlog.py \
		--external-items $(FEATURE_DIR)/backlog/github-issues.sample.json \
		--mapping mappings/github.mapping.json \
		--backlog $(FEATURE_DIR)/backlog/backlog.json

sync-github-project:
	python3 scripts/sync_github_project.py \
		--project-export $(FEATURE_DIR)/backlog/github-project.sample.json \
		--backlog $(FEATURE_DIR)/backlog/backlog.json


sync-command-center-board:
	python3 scripts/sync_backlog.py \
		--external-items $(FEATURE_DIR)/backlog/command-center-kanban.sample.json \
		--mapping mappings/command-center-kanban.mapping.json \
		--backlog $(FEATURE_DIR)/backlog/backlog.json

enrich-portfolio:
	python3 scripts/enrich_backlog_with_portfolio.py \
		--backlog $(FEATURE_DIR)/backlog/backlog.json \
		--portfolio $(FEATURE_DIR)/portfolio/projects.json \
		--out $(FEATURE_DIR)/backlog/backlog.json

schedule-backlog:
	python3 scripts/schedule_backlog.py \
		--backlog $(FEATURE_DIR)/backlog/backlog.json \
		--policy policies/priority-policy.json \
		--decision-context $(FEATURE_DIR)/knowledge/injected-context.json \
		--out $(FEATURE_DIR)/backlog/ranked-backlog.json


gate-with-context:
	python3 scripts/evaluate_ship_gate.py \
		--policy $(FEATURE_DIR)/policies/gate-policy.json \
		--verification-results $(FEATURE_DIR)/reports/verification-results.json \
		--review-report $(FEATURE_DIR)/reports/review-report.json \
		--qa-report $(FEATURE_DIR)/reports/qa-report.json \
		--decision-context $(FEATURE_DIR)/knowledge/injected-context.json \
		--out $(FEATURE_DIR)/reports/ship-decision.json

test-gate:
	bash tests/test_ship_gate.sh

all: validate verify gate


sync-and-plan: sync-backlog sync-github-project enrich-portfolio schedule-backlog


plan-change-bundles:
	python3 scripts/plan_change_bundles.py \
		--change-bundles $(FEATURE_DIR)/change-bundles/change-bundles.json \
		--out $(FEATURE_DIR)/change-bundles/ranked-change-bundles.json


inject-knowledge:
	python3 scripts/resolve_knowledge_context.py \
		--registry $(FEATURE_DIR)/knowledge/module-registry.json \
		--major-project-id $(MAJOR_PROJECT_ID) \
		--product-id "$(PRODUCT_ID)" \
		--repos "$(REPOS)" \
		--tags "$(TAGS)" \
		--change-bundles $(FEATURE_DIR)/change-bundles/change-bundles.json \
		--out-json $(FEATURE_DIR)/knowledge/injected-context.json \
		--out-md $(FEATURE_DIR)/knowledge/injected-context.md

plan-adaptive-workflow:
	python3 scripts/plan_adaptive_workflow.py \
		--request-profile $(FEATURE_DIR)/workflow/request-profile.json \
		--out $(FEATURE_DIR)/workflow/selected-stages.json

resolve-extensions:
	python3 scripts/resolve_extensions.py \
		--catalog $(FEATURE_DIR)/extensions/extensions-catalog.json \
		--selections $(FEATURE_DIR)/extensions/extension-selections.json \
		--out $(FEATURE_DIR)/extensions/resolved-extensions.json

select-workflow-lane:
	python3 scripts/select_workflow_lane.py \
		--request-profile $(FEATURE_DIR)/workflow/request-profile.json \
		--out $(FEATURE_DIR)/workflow/selected-lane.json

render-lite-issue:
	python3 scripts/render_github_issue_from_lite.py \
		--investigation $(FEATURE_DIR)/lite/investigation.json \
		--fix $(FEATURE_DIR)/lite/fix.json \
		--out $(FEATURE_DIR)/lite/github-issue.md
