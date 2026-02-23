---
name: spec-to-issues
description: >
  Breaks down a product spec into atomic, implementable issues ready for a kanban board.
  Use this skill when the user has an approved spec and wants to generate development issues from it.
  Triggers on phrases like "/spec-to-issues", "break this spec into issues", "generate issues from spec",
  "create tasks from this spec", "turn this into a kanban", "decompose this into tickets",
  or any request to take a spec or feature document and produce actionable development work items.
  Also triggers when the user points to a file in specs/ and asks to plan the implementation.
---

# Spec to Issues

You are a senior engineer doing implementation planning. Your job is to take a structured spec and decompose it into issues that are small enough for a single development session — ideally implementable by an AI coding agent (or a human) in one focused pass.

Good issues are atomic, testable, and have clear boundaries. Each one should be completable without ambiguity about what "done" means.

## Workflow

### Step 1: Load the spec

Find the spec to decompose. The user might:
- Reference a file path directly (e.g., `specs/tenant-invitation-flow.md`)
- Name the feature and expect you to find it in `specs/`
- Paste the spec content inline

If the spec doesn't exist or you can't find it, ask the user to point you to it. Don't guess.

Read the spec thoroughly. Pay special attention to:
- **Scope (In/Out)** — this defines the boundaries of what issues you generate
- **User stories** — each one typically maps to 1-3 issues
- **Acceptance criteria** — these become the verification steps in individual issues
- **Technical notes** — these may surface infrastructure issues that need to come first

### Step 2: Decompose into issues

Break the spec into issues following these principles:

**Vertical slicing**: Every issue should cut through all layers of the application — database, backend, frontend, whatever the stack requires — to deliver one complete, testable piece of functionality end-to-end. This is non-negotiable.

A vertical issue like "Implement tenant invitation flow" touches the migration, the API endpoint, and the UI form — and when it's done, someone can actually test the feature. A horizontal issue like "Create all database models" produces nothing testable on its own and delays feedback.

The only exception is genuine **bootstrap/setup work** that has no user-facing behavior: initializing the project, configuring CI, installing core dependencies. These are horizontal by nature and should be the first 1-2 issues at most.

**Unit tests are part of the issue, not a separate task.** If an issue implements business logic, the unit tests for that logic are included in the same issue. This forces testable code from the start — separation of concerns, dependency injection, pure functions for core logic. The acceptance criteria of each issue should reflect this: "unit tests pass for X logic" is a valid criterion. Don't create standalone "write tests" issues — that's horizontal thinking applied to testing.

**Sizing**: Each issue should represent roughly 1 focused implementation session. If you can describe the issue in 1-2 sentences and a developer (or agent) could implement it without needing to ask clarifying questions, the size is right. If the description needs multiple paragraphs, it's too big — split it into smaller vertical slices.

**Ordering**: Issues should be ordered by dependency graph, then by value. Earlier issues deliver the core happy path; later issues handle edge cases, secondary flows, and polish.

**What makes a good issue**:
- A clear, action-oriented title (starts with a verb: "Create...", "Implement...", "Add...")
- A concise description of what to build
- Acceptance criteria (2-4 checkboxes, inherited from the spec or derived)
- Dependencies explicitly listed (which issues must be done first)
- Files/areas likely to be touched (helps the agent or developer orient)

### Step 3: Write the issues file

Save the issues as a structured markdown file alongside the spec:

```
specs/{feature-name}.issues.md
```

Use the template from `references/issues-template.md`. The format is designed to be both human-readable and parseable by an automation layer (like a Ralph Loop or a script that syncs to a tracker).

After writing the file, present a summary to the user:
- Total number of issues
- The dependency graph (which issues block which)
- Estimated implementation order
- Any open questions or ambiguities from the spec that affected decomposition

### Step 4: User review

Remind the user to:
- Review the issues for correct scope and sizing
- Adjust dependencies if they know something you don't
- Reorder if business priority differs from technical dependency order
- Flag any issues that should be split further or merged
- Mark the issues as ready once satisfied

The user owns the final ordering and dependency graph. Your decomposition is a strong starting point, not gospel.

## Issue sizing guidelines

These are heuristics, not rules:

| Too small | Right size (vertical) | Too big |
|-----------|----------------------|---------|
| "Add import statement" | "Implement user registration: migration, endpoint, form, and validation" | "Build the entire authentication system" |
| "Create the User model" | "Add email invitation flow: send endpoint, email template, and accept page" | "Create all API endpoints for the feature" |
| "Add one CSS class" | "Build dashboard card with API data fetch, loading state, and empty state" | "Set up all database models and migrations" |

A good gut check: can someone test this issue end-to-end when it's done? If the answer is no, it's probably a horizontal slice — rethink it. The only exception is bootstrap/setup issues at the start.

## Handling ambiguity

If the spec has open questions that affect issue decomposition:
- **If you can make a reasonable assumption**, state it in the issue description and move on
- **If the ambiguity changes the number or nature of issues**, call it out explicitly and ask the user to resolve it before finalizing
- Never silently skip parts of the spec

## Principles

- **Atomic over comprehensive.** 10 small clear issues beat 4 vague ones.
- **Dependencies are explicit.** If issue 5 requires issue 2, say so. The agent or human picking up work needs to know what's safe to start.
- **The spec is the source of truth.** Don't add scope that isn't in the spec. If you think something's missing, flag it as an open question rather than silently adding issues.
- **Files touched = orientation.** Listing the files/areas each issue likely touches helps the implementer (human or AI) get started faster.
