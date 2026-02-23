# {Feature Name} — Issues

**Spec:** `specs/{feature-name}.md`
**Generated:** {date}
**Total issues:** {count}

## Dependency Graph

```
issue-1 (no deps)
issue-2 (no deps)
issue-3 → depends on: issue-1
issue-4 → depends on: issue-1, issue-2
issue-5 → depends on: issue-3, issue-4
```

## Implementation Order

A suggested sequence respecting dependencies. Issues at the same level can be worked in parallel.

1. issue-1, issue-2 _(parallel, no blockers)_
2. issue-3, issue-4
3. issue-5

---

## Issues

### ISSUE-1: {Verb} {concise description}

**Dependencies:** none
**Complexity:** S | M | L
**Files likely touched:** `src/models/user.ts`, `prisma/schema.prisma`

{2-4 sentence description of what to build and why. Reference the spec section this comes from if helpful. Include any assumptions made.}

**Acceptance criteria:**
- [ ] {Testable condition}
- [ ] {Another testable condition}
- [ ] {Edge case or validation}

---

### ISSUE-2: {Verb} {concise description}

**Dependencies:** none
**Complexity:** S | M | L
**Files likely touched:** `src/components/Dashboard.tsx`

{Description}

**Acceptance criteria:**
- [ ] {Testable condition}
- [ ] {Another testable condition}

---

<!-- Repeat for each issue. Keep the format consistent — the structure is designed
     to be parseable by scripts that sync issues to project trackers. -->

<!--
FORMATTING RULES (for parseability):
- Issue titles: ### ISSUE-{N}: {title}
- Dependencies: comma-separated ISSUE-{N} references, or "none"
- Complexity: exactly one of S, M, L
- Acceptance criteria: markdown checkboxes (- [ ])
- Separator: --- between issues
-->
