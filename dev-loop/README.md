# dev-loop

Bash-orchestrated development loop that invokes Claude Code CLI to implement issues one by one with human review between each.

## How it works

```
┌─────────────────────────────────────────┐
│            dev-loop.sh                   │
│                                          │
│  1. Parse .issues.md (Python)            │
│  2. Find next Ready issue (no blocked    │
│     deps)                                │
│  3. Update status → In Progress          │
│  4. Invoke: claude -p "implement this"   │
│     ↳ Fresh context window               │
│     ↳ Gets issue + spec as context       │
│     ↳ Implements, commits, exits         │
│  5. Update status → In Review            │
│  6. Human reviews:                       │
│     ├─ approve → Done, next issue        │
│     ├─ reject  → claude -p "fix this"    │
│     ├─ diff    → show changes            │
│     └─ skip    → back to Ready           │
│  7. Repeat until no more issues          │
└─────────────────────────────────────────┘
```

## Usage

```bash
# From your project root
./path/to/dev-loop.sh specs/my-feature.issues.md
```

The script will:
- Create/switch to a `feat/{feature-name}` branch
- Show the current backlog summary
- Start picking up Ready issues in order

## Requirements

- `claude` CLI installed and authenticated
- Python 3.10+
- Git repo initialized

## Files

| File | Purpose |
|------|---------|
| `dev-loop.sh` | Main orchestrator — the loop logic |
| `parse-issues.py` | Parses `.issues.md` format, manages status transitions |
