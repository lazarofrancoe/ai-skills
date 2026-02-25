#!/usr/bin/env python3
"""
sync-to-tracker.py — Syncs .issues.md state to a project tracker

Reads the issues file, compares with last known sync state, and pushes
changes to the configured tracker (Monday, Jira, GitHub Projects, etc).

Usage:
  ./sync-to-tracker.py specs/feature.issues.md              # sync
  ./sync-to-tracker.py specs/feature.issues.md --init        # first-time setup
  ./sync-to-tracker.py specs/feature.issues.md --dry-run     # preview changes
  ./sync-to-tracker.py specs/feature.issues.md --status      # show sync state

Config: .sync-config.json in project root
State:  .sync-state.json in project root (auto-generated, commit to repo)
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path

# Add parent dir so we can import parse-issues
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "dev-loop"))
from importlib import import_module


def load_config() -> dict:
    """Load tracker config from .sync-config.json"""
    config_path = Path(".sync-config.json")
    if not config_path.exists():
        print("ERROR: .sync-config.json not found in project root.", file=sys.stderr)
        print("\nCreate one with:", file=sys.stderr)
        print(json.dumps(CONFIG_TEMPLATE, indent=2), file=sys.stderr)
        sys.exit(1)
    return json.loads(config_path.read_text())


def load_sync_state(issues_file: str) -> dict:
    """Load the sync state mapping for this issues file."""
    state_path = Path(".sync-state.json")
    if not state_path.exists():
        return {}
    all_state = json.loads(state_path.read_text())
    return all_state.get(issues_file, {})


def save_sync_state(issues_file: str, state: dict):
    """Save the sync state mapping."""
    state_path = Path(".sync-state.json")
    all_state = {}
    if state_path.exists():
        all_state = json.loads(state_path.read_text())
    all_state[issues_file] = state
    state_path.write_text(json.dumps(all_state, indent=2) + "\n")


def get_adapter(config: dict, issues_file: str = ""):
    """Load the appropriate tracker adapter."""
    tracker = config.get("tracker")
    if not tracker:
        print("ERROR: 'tracker' not specified in .sync-config.json", file=sys.stderr)
        sys.exit(1)

    adapter_module = f"adapters.{tracker}"
    try:
        mod = import_module(adapter_module)
        return mod.Adapter(config, issues_file=issues_file)
    except ModuleNotFoundError:
        available = [p.stem for p in (SCRIPT_DIR / "adapters").glob("*.py") if p.stem != "__init__" and p.stem != "base"]
        print(f"ERROR: Unknown tracker '{tracker}'", file=sys.stderr)
        print(f"Available: {', '.join(available)}", file=sys.stderr)
        sys.exit(1)


def parse_issues_file(filepath: str) -> list[dict]:
    """Parse the issues file using the dev-loop parser."""
    sys.path.insert(0, str(SCRIPT_DIR.parent / "dev-loop"))
    from pathlib import Path as P
    # Import inline to avoid circular deps
    parse_mod_path = SCRIPT_DIR.parent / "dev-loop" / "parse-issues.py"
    if not parse_mod_path.exists():
        print(f"ERROR: parse-issues.py not found at {parse_mod_path}", file=sys.stderr)
        sys.exit(1)

    import importlib.util
    spec = importlib.util.spec_from_file_location("parse_issues", str(parse_mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_issues(filepath)


# --- Status mapping ---------------------------------------------------------
# Maps .issues.md statuses to a normalized set. Each adapter translates these
# to tracker-specific values.
NORMALIZED_STATUSES = {
    "Backlog": "backlog",
    "Ready": "ready",
    "In Progress": "in_progress",
    "In Review": "in_review",
    "Done": "done",
}


CONFIG_TEMPLATE = {
    "tracker": "monday",
    "monday": {
        "api_token": "YOUR_MONDAY_API_TOKEN",
        "board_id": "YOUR_BOARD_ID",
        "group_mapping": {
            "specs/feature.issues.md": "GROUP_ID_FOR_FEATURE",
            "default": "GROUP_ID_FOR_UNGROUPED"
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


# --- Colors -----------------------------------------------------------------
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'


def extract_human_summary(raw_block: str) -> str:
    """Extract a clean, human-readable summary from a raw issue block.
    
    Pulls out:
    - The description paragraph (the prose explaining what to build)
    - The acceptance criteria checklist
    
    Strips all metadata fields (Status, Dependencies, Complexity, etc.)
    since those are for the tooling, not for humans reading Monday.
    """
    lines = raw_block.split('\n')
    
    description_lines = []
    acceptance_lines = []
    section = None
    
    # Fields to skip — these are metadata, not content
    metadata_prefixes = (
        '### ISSUE-', '**Status:**', '**Dependencies:**', '**Complexity:**',
        '**Layers:**', '**Files likely touched:**', '**Dev notes:**',
    )
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines at the start
        if not stripped and not description_lines and section is None:
            continue

        # Skip markdown headers (##, ###, etc.)
        if stripped.startswith('#'):
            continue
            
        # Skip metadata fields
        if any(stripped.startswith(prefix) for prefix in metadata_prefixes):
            continue
        
        # Detect acceptance criteria section
        if stripped.startswith('**Acceptance criteria:**'):
            section = 'acceptance'
            continue
        
        # Collect acceptance criteria checkboxes
        if section == 'acceptance':
            if stripped.startswith('- ['):
                # Convert markdown checkbox to plain text
                criterion = stripped.replace('- [x] ', '✅ ').replace('- [ ] ', '☐ ')
                acceptance_lines.append(criterion)
            elif stripped and not stripped.startswith('**'):
                acceptance_lines.append(stripped)
            elif stripped.startswith('**'):
                section = None  # Hit next field, stop
        
        # Collect description (prose paragraphs between metadata and acceptance)
        elif section is None and stripped and not stripped.startswith('**'):
            description_lines.append(stripped)
    
    parts = []
    if description_lines:
        parts.append('\n'.join(description_lines))
    if acceptance_lines:
        parts.append('\nCriteria:\n' + '\n'.join(acceptance_lines))
    
    return '\n'.join(parts) if parts else ''


def _hash(text: str) -> str:
    """Short hash of text content for change detection."""
    return hashlib.md5(text.encode()).hexdigest()[:12] if text else ""


def sync(issues_file: str, dry_run: bool = False):
    """Main sync logic."""
    config = load_config()
    adapter = get_adapter(config, issues_file=issues_file)
    state = load_sync_state(issues_file)
    issues = parse_issues_file(issues_file)

    created = 0
    updated = 0
    unchanged = 0
    archived = 0

    issue_ids = {issue["id"] for issue in issues}

    # --- Archive orphaned issues (in state but not in .issues.md) -----------
    orphaned = [iid for iid in list(state.keys()) if iid not in issue_ids]
    for issue_id in orphaned:
        tracker_item = state[issue_id]
        if dry_run:
            print(f"  {RED}[ARCHIVE]{NC}  {issue_id}  (removed from .issues.md)")
        else:
            adapter.archive_item(tracker_item["tracker_id"])
            del state[issue_id]
            print(f"  {RED}✓ Archived{NC}  {issue_id}")
        archived += 1

    # --- Create / update issues ---------------------------------------------
    for issue in issues:
        issue_id = issue["id"]
        normalized_status = NORMALIZED_STATUSES.get(issue["status"], "backlog")
        tracker_item = state.get(issue_id)
        summary = extract_human_summary(issue.get("raw_block", ""))
        summary_hash = _hash(summary)

        if tracker_item is None:
            # --- New issue: create in tracker --------------------------------
            if dry_run:
                print(f"  {GREEN}[CREATE]{NC}  {issue_id}: {issue['title']}  →  {normalized_status}")
            else:
                tracker_id = adapter.create_item(
                    title=f"{issue_id}: {issue['title']}",
                    status=normalized_status,
                    description=summary,
                    complexity=issue.get("complexity", "M"),
                    layers=issue.get("layers", ""),
                )
                state[issue_id] = {
                    "tracker_id": tracker_id,
                    "last_status": normalized_status,
                    "description_hash": summary_hash,
                }
                print(f"  {GREEN}✓ Created{NC}  {issue_id}: {issue['title']}  →  {tracker_id}")
            created += 1

        else:
            # --- Existing issue: check for changes ---------------------------
            status_changed = tracker_item.get("last_status") != normalized_status
            desc_changed = tracker_item.get("description_hash") != summary_hash

            if status_changed:
                if dry_run:
                    print(f"  {YELLOW}[UPDATE]{NC}  {issue_id}: {tracker_item['last_status']} → {normalized_status}")
                else:
                    adapter.update_status(
                        tracker_id=tracker_item["tracker_id"],
                        status=normalized_status,
                    )
                    state[issue_id]["last_status"] = normalized_status
                    # Backfill hash if missing
                    if "description_hash" not in state[issue_id]:
                        state[issue_id]["description_hash"] = summary_hash
                    print(f"  {YELLOW}✓ Status{NC}  {issue_id}: → {normalized_status}")
                updated += 1

            elif desc_changed and summary and "description_hash" in tracker_item:
                # Only push description if hash existed before (not first-time backfill)
                if dry_run:
                    print(f"  {CYAN}[DESC]{NC}  {issue_id}: description changed")
                else:
                    adapter.update_description(
                        tracker_id=tracker_item["tracker_id"],
                        description=summary,
                    )
                    state[issue_id]["description_hash"] = summary_hash
                    print(f"  {CYAN}✓ Desc{NC}  {issue_id}: description updated")
                updated += 1

            else:
                # Backfill hash silently if missing
                if "description_hash" not in tracker_item:
                    state[issue_id]["description_hash"] = summary_hash
                unchanged += 1

    if not dry_run:
        save_sync_state(issues_file, state)

    # --- Summary
    print()
    label = "[DRY RUN] " if dry_run else ""
    print(f"  {label}{GREEN}{created} created{NC}  {YELLOW}{updated} updated{NC}  {RED}{archived} archived{NC}  {unchanged} unchanged")


def show_status(issues_file: str):
    """Show current sync state."""
    state = load_sync_state(issues_file)
    issues = parse_issues_file(issues_file)

    if not state:
        print("  No sync state found. Run with --init or sync first.")
        return

    for issue in issues:
        issue_id = issue["id"]
        tracker_item = state.get(issue_id)
        if tracker_item:
            synced = f"{GREEN}synced{NC} → {tracker_item['tracker_id']}  (last: {tracker_item['last_status']})"
        else:
            synced = f"{RED}not synced{NC}"
        print(f"  {issue_id}: {issue['title']}  [{synced}]")


def resync_descriptions(issues_file: str, dry_run: bool = False):
    """Re-push descriptions for all synced issues."""
    config = load_config()
    adapter = get_adapter(config, issues_file=issues_file)
    state = load_sync_state(issues_file)
    issues = parse_issues_file(issues_file)

    if not state:
        print("  No sync state found. Run sync first to create issues.")
        return

    updated = 0
    skipped = 0

    for issue in issues:
        issue_id = issue["id"]
        tracker_item = state.get(issue_id)

        if not tracker_item:
            skipped += 1
            continue

        summary = extract_human_summary(issue.get("raw_block", ""))
        if not summary:
            skipped += 1
            continue

        if dry_run:
            print(f"  {YELLOW}[RESYNC]{NC}  {issue_id}: {issue['title']}")
        else:
            adapter.update_description(tracker_item["tracker_id"], summary)
            state[issue_id]["description_hash"] = _hash(summary)
            print(f"  {YELLOW}✓ Updated{NC}  {issue_id}: {issue['title']}")
        updated += 1

    if not dry_run:
        save_sync_state(issues_file, state)

    print()
    label = "[DRY RUN] " if dry_run else ""
    print(f"  {label}{YELLOW}{updated} updated{NC}  {skipped} skipped")


# --- CLI --------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Sync .issues.md to project tracker")
    parser.add_argument("issues_file", help="Path to .issues.md file")
    parser.add_argument("--init", action="store_true", help="Initialize: create all issues in tracker")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without syncing")
    parser.add_argument("--resync", action="store_true", help="Re-push descriptions for all existing issues")
    parser.add_argument("--status", action="store_true", help="Show current sync state")

    args = parser.parse_args()

    if not Path(args.issues_file).exists():
        print(f"ERROR: {args.issues_file} not found", file=sys.stderr)
        sys.exit(1)

    print()
    print(f"  {BOLD}{CYAN}sync-to-tracker{NC}  ←  {args.issues_file}")
    print()

    if args.status:
        show_status(args.issues_file)
    elif args.resync:
        resync_descriptions(args.issues_file, dry_run=args.dry_run)
    else:
        sync(args.issues_file, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
