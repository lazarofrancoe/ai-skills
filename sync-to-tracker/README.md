# sync-to-tracker

Syncs `.issues.md` state to a project tracker. Currently supports Monday.com, with a plugin architecture for adding others.

## How it works

```
.issues.md  ──→  sync-to-tracker.py  ──→  Monday / Jira / GitHub Projects
                        │
                  .sync-state.json (mapping: ISSUE-N → tracker ID)
```

The sync is **one-directional**: repo → tracker. The `.issues.md` file is the source of truth; the tracker is a view into it.

## Setup

### 1. Create `.sync-config.json` in your project root

```json
{
    "tracker": "monday",
    "monday": {
        "api_token": "your-monday-api-token",
        "board_id": "5026547200",
        "group_mapping": {
            "specs/migration.issues.md": "migration_group_id",
            "specs/waitlist.issues.md": "waitlist_group_id",
            "default": "general_group_id"
        },
        "status_column_id": "status",
        "status_mapping": {
            "backlog": "Backlog",
            "ready": "Ready",
            "in_progress": "In Progress",
            "in_review": "In Review",
            "done": "Done"
        }
    }
}
```

**Where to find these values:**
- `api_token`: monday.com → Profile picture → Admin → API
- `board_id`: From the board URL: `monday.com/boards/{board_id}`
- `group IDs`: monday.com/developers/v2/try-it-yourself → query `boards(ids: [...]) { groups { id title } }`
- `status_column_id`: Board settings → Columns → click the status column → see ID

Each `.issues.md` file maps to a Monday group. The `default` key is used as fallback for unmapped files.

### 2. Run initial sync

```bash
# Preview what will be created
./sync-to-tracker.py specs/my-feature.issues.md --dry-run

# Create all issues in tracker
./sync-to-tracker.py specs/my-feature.issues.md --init
```

This creates a `.sync-state.json` file that maps `ISSUE-N` to tracker item IDs. **Commit this file to your repo.**

### 3. Ongoing sync

```bash
# Sync after status changes
./sync-to-tracker.py specs/my-feature.issues.md

# Check sync state
./sync-to-tracker.py specs/my-feature.issues.md --status
```

## Auto-sync with dev-loop

If `.sync-config.json` exists in your project root, `dev-loop.sh` will automatically sync after every status transition. No extra setup needed.

## Adding a new tracker

1. Create `adapters/your_tracker.py`
2. Implement a class `Adapter(BaseAdapter)` with `create_item()` and `update_status()`
3. Set `"tracker": "your_tracker"` in `.sync-config.json`

See `adapters/__init__.py` for the interface and `adapters/monday.py` for a reference implementation.

## Files

| File | Purpose |
|------|---------|
| `sync-to-tracker.py` | Main script — reads issues, diffs state, calls adapter |
| `adapters/__init__.py` | Base adapter interface |
| `adapters/monday.py` | Monday.com adapter (GraphQL API) |
| `adapters/github.py` | GitHub Projects adapter (skeleton) |
