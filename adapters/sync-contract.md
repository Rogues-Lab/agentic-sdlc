# Sync Contract

## Input
- `external-items.json`: array of items from a source system API export.
- `mapping.json`: field mapping file for that source.
- `backlog.json`: canonical backlog file.

## Output
- Updated `backlog.json` with upserted items by `(source.system, source.scope, source.external_id)`.
- New items default to `status: todo`, owner `cto`, and baseline priority inputs.

## Rules
- Existing items retain manually curated fields unless source mapping explicitly overwrites.
- `updated_at` from source always refreshes.
- Source IDs are immutable after first sync.


For GitHub Projects with multiple repositories, set `source.scope` to `<owner>/<repo>`.
