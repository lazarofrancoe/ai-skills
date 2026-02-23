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

### ISSUE-1: {Verb} {concise description of end-to-end functionality}

**Dependencies:** none
**Complexity:** S | M | L
**Layers:** DB | Backend | Frontend _(list all layers this issue touches)_
**Files likely touched:** `src/models/user.ts`, `src/api/users.ts`, `src/pages/Register.tsx`

{2-4 sentence description of what to build and why. Describe the complete vertical slice: what the user does, what happens in the backend, what gets persisted. Reference the spec section this comes from if helpful.}

**Acceptance criteria:**
- [ ] {Testable end-to-end condition}
- [ ] {Another testable condition}
- [ ] {Unit tests pass for business logic (e.g., validation rules, calculations, state transitions)}
- [ ] {Edge case or validation}

---

### ISSUE-2: {Verb} {concise description of end-to-end functionality}

**Dependencies:** none
**Complexity:** S | M | L
**Layers:** DB | Backend | Frontend
**Files likely touched:** `src/components/Dashboard.tsx`, `src/api/dashboard.ts`

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
- Layers: pipe-separated list of layers touched (e.g., DB | Backend | Frontend)
- Acceptance criteria: markdown checkboxes (- [ ])
- Separator: --- between issues
-->
