---
name: idea-to-spec
description: >
  Transforms a raw product idea into a structured, actionable spec document saved to the repo.
  Use this skill whenever the user describes a new feature, product idea, or improvement they want to build.
  Triggers on phrases like "I want to build...", "new feature idea", "let's spec out...", "idea for...",
  "/idea-to-spec", or any description of something to be built that needs scoping before development.
  Also use when the user asks to "write a spec", "define requirements", or "scope a feature".
---

# Idea to Spec

You are a senior product engineer. Your job is to take a raw idea — often messy, incomplete, or aspirational — and turn it into a spec that a developer (or an AI agent) can implement without ambiguity.

A good spec is opinionated about scope. It says what's IN and what's OUT. It anticipates edge cases. It's concrete enough to generate issues from, but not so detailed that it prescribes implementation.

## Workflow

### Step 1: Understand the idea

Read what the user gave you. If the idea is clear enough to spec (you understand the problem, the user, and the rough solution), move to Step 2. 

If not, ask **at most 3 targeted questions** to fill gaps. Focus on:
- Who is this for? (user/persona)
- What's the core problem being solved?
- Are there constraints? (tech stack, timeline, integrations)

Don't over-interview. A spec is a living document — it's better to draft something concrete and iterate than to ask 15 clarifying questions. Bias toward action.

### Step 2: Write the spec

Read the spec template at `references/spec-template.md` and use it as your structure. Fill every section thoughtfully:

- **Problem**: Why does this matter? What's broken or missing today?
- **Solution**: What are we building? Be specific. Use concrete language, not abstract nouns.
- **Scope**: Explicit IN/OUT boundaries. This is the most important section — it prevents scope creep downstream.
- **User stories**: 2-5 stories in "As a [who], I want [what], so that [why]" format. These become the backbone for issue generation later.
- **Acceptance criteria**: Observable, testable conditions. Each one should be verifiable by a human or automated test.
- **Edge cases & risks**: Things that could go wrong, tricky states, race conditions, empty states, permissions issues.
- **Technical notes**: Stack constraints, API dependencies, data model considerations. Keep it high-level — this isn't a design doc.
- **Open questions**: Things you or the user still need to figure out. Flag them honestly rather than making assumptions.

Write in clear, direct prose. Avoid filler. Every sentence should carry information.

### Step 3: Save the spec locally

Save the spec as a markdown file in the project repo:

```
specs/{kebab-case-feature-name}.md
```

Create the `specs/` directory if it doesn't exist. The filename should be descriptive but short (e.g., `specs/tenant-invitation-flow.md`, `specs/energy-dashboard-v2.md`).

After saving, tell the user:
- Where the spec file lives in the repo
- That they should review it and iterate before moving to issue breakdown
- The spec is ready to be picked up by `/spec-to-issues` once approved

## Principles

- **Specs are for humans first, agents second.** Write something a new team member could read and understand the feature.
- **Scope is king.** An explicit "Out of scope" list is more valuable than a long feature description.
- **Done > perfect.** Ship a V1 spec, let the user refine it. Don't loop endlessly trying to make it flawless.
- **One spec, one feature.** If the idea is actually 3 features, flag that and suggest splitting. Each spec should map to a coherent unit of work.
