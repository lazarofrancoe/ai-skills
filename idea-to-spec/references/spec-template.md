# {Feature Name}

**Author:** {name}
**Date:** {date}
**Spec file:** `specs/{filename}.md`

---

## Problem

What's broken, missing, or suboptimal today? Why should we build this? Ground it in user pain or business impact. Be specific — "users are frustrated" is weak; "field workers spend ~15 min/day manually reconciling cooler status because there's no sync between the app and the dashboard" is strong.

## Solution

What are we building? Describe the feature in concrete terms. A reader should be able to picture what the user sees and does.

If there's a key insight or approach that makes this solution non-obvious, explain it here.

## Scope

### In scope
- Bullet each concrete deliverable or behavior
- Be specific: "REST endpoint for X", "UI screen for Y", "cron job that does Z"

### Out of scope
- Explicitly list what we are NOT building in this iteration
- This prevents scope creep and sets expectations with stakeholders
- Things that might seem obviously included but aren't should be called out here

## User Stories

- As a **{persona}**, I want **{action}**, so that **{benefit}**.
- As a **{persona}**, I want **{action}**, so that **{benefit}**.
- As a **{persona}**, I want **{action}**, so that **{benefit}**.

Keep to 2-5 stories. Each one should represent a distinct interaction or value stream. These will become the foundation for issue breakdown in the next phase.

## Acceptance Criteria

Each criterion should be independently testable. Write them as "Given/When/Then" or as simple assertions.

- [ ] {Observable condition that proves the feature works}
- [ ] {Another testable condition}
- [ ] {Edge case that must be handled}
- [ ] {Performance or reliability requirement, if applicable}

## Edge Cases & Risks

Think about: empty states, error states, permissions, concurrent access, data migration, backwards compatibility, mobile vs desktop, slow networks, large datasets.

| Scenario | Risk | Mitigation |
|----------|------|------------|
| {What could happen} | {Impact} | {How we handle it} |

## Technical Notes

High-level technical considerations. Not a design doc — just enough context for whoever breaks this into issues.

- **Stack/dependencies**: Any specific tech requirements or constraints
- **Data model**: New entities, relationships, or migrations needed
- **Integrations**: External APIs, services, or systems involved
- **Performance**: Expected load, latency requirements, caching strategy

## Open Questions

Things that still need answers before or during implementation. Be honest about uncertainty — it's better to flag a question than to make a silent assumption.

- [ ] {Question that needs an answer}
- [ ] {Decision that hasn't been made yet}
