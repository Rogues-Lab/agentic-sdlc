# Using the Agentic SDLC Pack in an Instance

This pack is a **generic framework**. To use it for real delivery you create an
**instance** — a copy of the pack customized with *your* projects, repos,
standards, and policies. This guide explains the model and the setup.

---

## 1. Framework vs. instance

| | **The pack** (this repo) | **An instance** (your copy) |
|---|---|---|
| Purpose | Reusable process + automation | Real delivery for one org/agent |
| Contains | Scripts, schemas, templates, gate logic, example data | The framework **+ your reality** |
| Project data | Examples only (`film-fun`, `openclaw`) | *Your* portfolio, knowledge modules, resolver rules, policies |
| Changes when | The *process* improves | *Your projects or standards* change |

The rule of thumb:

> **Process improvements** (a script fix, a new gate rule, a new template) belong
> in the pack and flow *down* into instances. **Your projects and standards**
> belong in the instance and never flow back up.

An instance owns these files; everything else is framework and should track the
pack:

- `project-template/portfolio/projects.json` — your major projects → repos
- `project-template/knowledge/module-registry.json` — your resolver rules
- `project-template/knowledge/**` — your standards/architecture module content
- `project-template/policies/gate-policy.json` — your ship policy
- `automation/*` — wired to your runtime
- `AGENTS.md` / `docs/` — your operating notes

---

## 2. Create an instance

An instance is a full copy of the pack with its own git history.

```bash
# Option A: clone the framework and re-point the remote
git clone git@github.com:Rogues-Lab/agentic-sdlc.git my-instance
cd my-instance
git remote rename origin upstream          # keep the pack as 'upstream' for syncing (§6)
git remote add origin <your-instance-remote>

# Option B: package the pack and extract it elsewhere
./scripts/export_pack.sh                    # -> dist/agentic-sdlc-pack-<ts>.tar.gz
```

Smoke-test the copy before customizing:

```bash
make validate && make verify && make gate
```

> `scripts/bootstrap_project.sh <dir>` is a *different* tool — it scaffolds a new
> **feature workspace** (artifacts/reports/policies for one feature) *inside* an
> instance. It does not create an instance.

---

## 3. Customize the instance (the instance-owned layer)

### a. Declare your projects
Edit `project-template/portfolio/projects.json` — map each major project to its
repos. One major project may span many repos:

```json
{
  "major_projects": [
    { "id": "my-platform", "name": "My Platform",
      "description": "Core delivery", "repos": ["org/api", "org/web"] }
  ]
}
```

### b. Add your standards as knowledge modules
Drop markdown standards under `project-template/knowledge/...`, then register and
wire them in `project-template/knowledge/module-registry.json`:

```json
{
  "module_library": [
    { "id": "platform-standards",
      "path": "project-template/knowledge/my-platform/standards.md",
      "tags": ["standards", "my-platform"] }
  ],
  "resolver_rules": [
    { "id": "platform-major", "priority": 200,
      "match": { "major_project_ids": ["my-platform"] },
      "module_ids": ["platform-standards"],
      "decision_overrides": {
        "quality_gates": { "required_check_types": ["unit", "integration"] }
      } }
  ]
}
```

Resolver rules match on `major_project_id`, `product_id`, `repos`
(exact/prefix/glob), `deployment_targets`, `change_bundle_ids`, and `tags`. They
apply in `(priority, id)` order; modules dedupe by `id`; `decision_overrides`
deep-merge. Verify resolution:

```bash
make inject-knowledge MAJOR_PROJECT_ID=my-platform REPOS=org/api
cat project-template/knowledge/injected-context.md
```

### c. Set your ship policy
Tune `project-template/policies/gate-policy.json` — required gates, blocked
severities, blocked check types, waiver policy.

### d. Wire automation
Point `automation/*` (taskflow/cron/hooks) at your runtime and external systems
(GitHub/Jira/Linear/Kanban mappings live in `mappings/`).

---

## 4. Deliver work in the instance

The everyday loop (see the README for full detail on each command):

```bash
make select-workflow-lane     # full vs lite for this request
make inject-knowledge         # resolve standards + decision_context for this work
# author artifacts under project-template/artifacts/ from templates/
make validate                 # traceability gate — run BEFORE building
make plan-change-bundles      # multi-repo / multi-deploy planning (if needed)
make verify                   # run verification checks
make gate-with-context        # ship decision, with injected overrides applied
make sync-and-plan            # pull external work + WSJF-rank the backlog
```

Stable IDs are mandatory throughout (`SPEC-* / REQ-* / AC-* / TKT-* / TEST-* /
CHECK-* / RVW-* / QA-*`) — they are what make traceability machine-checkable.

---

## 5. Document how your agent operates the instance

Add an `AGENTS.md` (and optionally `docs/*.md`) to your instance describing your
operating contract: which lane to pick when, how implementation is delegated,
which external systems are synced. Keep org standards in knowledge modules, not
hard-coded in prompts — resolve them at runtime via `make inject-knowledge`.

---

## 6. Keep the instance in sync with the pack

When the framework improves upstream, pull the **framework files** and leave your
**instance-owned files** (§1) untouched.

```bash
# with the pack as 'upstream' (Option A above)
git fetch upstream
git checkout upstream/main -- scripts schemas templates Makefile
# review, then smoke-test
make validate && make verify && make gate
```

If you copied rather than cloned, re-copy `scripts/`, `schemas/`, `templates/`,
and generic `automation/` from a fresh pack, then re-run the smoke test. Never
overwrite `portfolio/projects.json`, `module-registry.json`, your `knowledge/`
content, `policies/gate-policy.json`, `AGENTS.md`, or `docs/`.

---

## 7. Checklist for a new instance

- [ ] Copied/cloned the pack; remote re-pointed; `upstream` kept for syncing
- [ ] `make validate && make verify && make gate` pass on the fresh copy
- [ ] `portfolio/projects.json` lists your real major projects + repos
- [ ] Knowledge modules added and wired via `resolver_rules`
- [ ] `gate-policy.json` reflects your real ship criteria
- [ ] `automation/*` and `mappings/*` point at your runtime + trackers
- [ ] `AGENTS.md` documents how your agent operates this instance
