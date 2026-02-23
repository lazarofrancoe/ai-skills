#!/usr/bin/env python3
"""
parse-issues.py — Parser for .issues.md files

Commands:
  next <file>                     → Print next eligible issue (Ready + deps Done)
  detail <file> <issue_id>        → Print full issue block
  update-status <file> <id> <st>  → Update an issue's status in-place
  update-notes <file> <id> <note> → Append to an issue's dev notes
  summary <file>                  → Print one-line-per-issue summary
"""

import sys
import re
from pathlib import Path


def parse_issues(filepath: str) -> list[dict]:
    """Parse a .issues.md file into a list of issue dicts."""
    content = Path(filepath).read_text()
    issue_blocks = re.split(r'\n---\n', content)

    issues = []
    for block in issue_blocks:
        title_match = re.search(r'###\s+(ISSUE-\d+):\s*(.+)', block)
        if not title_match:
            continue

        issue_id = title_match.group(1)
        title = title_match.group(2).strip()

        status = _extract_field(block, 'Status') or 'Backlog'
        deps_raw = _extract_field(block, 'Dependencies') or 'none'
        complexity = _extract_field(block, 'Complexity') or 'M'
        layers = _extract_field(block, 'Layers') or ''
        files = _extract_field(block, 'Files likely touched') or ''

        deps = []
        if deps_raw.strip().lower() != 'none':
            deps = [d.strip() for d in re.findall(r'ISSUE-\d+', deps_raw)]

        issues.append({
            'id': issue_id,
            'title': title,
            'status': status.strip(),
            'dependencies': deps,
            'complexity': complexity.strip(),
            'layers': layers.strip(),
            'files': files.strip(),
            'raw_block': block.strip(),
        })

    return issues


def _extract_field(block: str, field_name: str) -> str | None:
    """Extract a **Field:** value from a markdown block."""
    pattern = rf'\*\*{re.escape(field_name)}:\*\*\s*(.+)'
    match = re.search(pattern, block)
    return match.group(1).strip() if match else None


def find_next_issue(issues: list[dict]) -> dict | None:
    """Find the next issue that is Ready and has all dependencies Done."""
    done_ids = {i['id'] for i in issues if i['status'] == 'Done'}

    for issue in issues:
        if issue['status'] != 'Ready':
            continue
        if all(dep in done_ids for dep in issue['dependencies']):
            return issue

    return None


def update_status(filepath: str, issue_id: str, new_status: str):
    """Update an issue's status in the file."""
    content = Path(filepath).read_text()

    # Find the status line after the issue header
    pattern = rf'(###\s+{re.escape(issue_id)}:.*?\n(?:.*?\n)*?)\*\*Status:\*\*\s*\S+'
    match = re.search(pattern, content)

    if not match:
        print(f"ERROR: Could not find status for {issue_id}", file=sys.stderr)
        sys.exit(1)

    # Simple replacement of the status value
    old_status_pattern = rf'(###\s+{re.escape(issue_id)}:.*?\n(?:.*?\n)*?\*\*Status:\*\*)\s*\S+'
    content = re.sub(
        old_status_pattern,
        rf'\g<1> {new_status}',
        content,
        count=1
    )

    Path(filepath).write_text(content)


def update_dev_notes(filepath: str, issue_id: str, notes: str):
    """Append to an issue's dev notes."""
    content = Path(filepath).read_text()

    # Find the dev notes field for this issue
    pattern = rf'(###\s+{re.escape(issue_id)}:.*?(?:\n.*?)*?\*\*Dev notes:\*\*)\s*(.*?)(?=\n---|\n###|\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        existing = match.group(2).strip()
        if existing and existing != '_(filled by dev-loop during implementation)_':
            new_notes = f"{existing}\n{notes}"
        else:
            new_notes = notes
        content = content[:match.start(2)] + f" {new_notes}" + content[match.end(2):]
        Path(filepath).write_text(content)
    else:
        print(f"WARNING: No dev notes field found for {issue_id}", file=sys.stderr)


def print_summary(issues: list[dict]):
    """Print a one-line summary per issue."""
    status_colors = {
        'Backlog': '\033[90m',      # gray
        'Ready': '\033[0;34m',      # blue
        'In Progress': '\033[1;33m', # yellow
        'In Review': '\033[0;35m',   # purple
        'Done': '\033[0;32m',       # green
    }
    nc = '\033[0m'

    for issue in issues:
        color = status_colors.get(issue['status'], nc)
        deps = ', '.join(issue['dependencies']) if issue['dependencies'] else '-'
        print(f"  {color}[{issue['status']:^12}]{nc}  {issue['id']}: {issue['title']}  (deps: {deps})")


# --- CLI --------------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    filepath = sys.argv[2]
    issues = parse_issues(filepath)

    if command == 'next':
        issue = find_next_issue(issues)
        if issue:
            print(issue['id'])
            print(issue['title'])
        else:
            print("NONE")

    elif command == 'detail':
        if len(sys.argv) < 4:
            print("Usage: parse-issues.py detail <file> <issue_id>", file=sys.stderr)
            sys.exit(1)
        issue_id = sys.argv[3]
        for issue in issues:
            if issue['id'] == issue_id:
                print(issue['raw_block'])
                sys.exit(0)
        print(f"ERROR: {issue_id} not found", file=sys.stderr)
        sys.exit(1)

    elif command == 'update-status':
        if len(sys.argv) < 5:
            print("Usage: parse-issues.py update-status <file> <issue_id> <status>", file=sys.stderr)
            sys.exit(1)
        update_status(filepath, sys.argv[3], sys.argv[4])

    elif command == 'update-notes':
        if len(sys.argv) < 5:
            print("Usage: parse-issues.py update-notes <file> <issue_id> <notes>", file=sys.stderr)
            sys.exit(1)
        update_dev_notes(filepath, sys.argv[3], sys.argv[4])

    elif command == 'summary':
        print_summary(issues)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
