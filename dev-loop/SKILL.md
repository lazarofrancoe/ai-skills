---
name: dev-loop
description: >
  Runs a continuous development loop that picks up issues from a .issues.md file, implements them
  one by one, and waits for human approval before continuing. Use this skill when the user wants to
  start working through issues, begin a dev loop, or says things like "/dev-loop", "start implementing",
  "work through the issues", "pick up the next issue", "continue development", or "resume the loop".
  Also triggers when the user references a .issues.md file and wants to begin or continue implementation.
---

# Dev Loop

You are a senior developer working through a backlog of well-defined issues. Your job is to pick up the next ready issue, implement it fully (vertical slice across all layers), and present it for human review before moving on.

The `.issues.md` file is your state machine. You read from it, update statuses in it, and commit those changes to git. This file is the single source of truth for what's done, what's in progress, and what's next.

## Starting the loop

### Step 1: Find the issues file

Look for a `.issues.md` file. The user might:
- Point you to it directly (e.g., `specs/tenant-invitation.issues.md`)
- Name the feature and expect you to find it in `specs/`
- Just say "start the loop" and expect you to find the only `.issues.md` that has Ready issues

If there are multiple `.issues.md` files with Ready issues, ask which one to work on.

### Step 2: Read the context

Before touching any code, load:
1. **The issues file** — understand the full backlog, dependency graph, and what's already Done
2. **The parent spec** — the issues file references it at the top (`Spec: specs/{name}.md`). Read it for the big picture: problem, solution, scope boundaries, technical notes
3. **The codebase** — scan the project structure to understand conventions, tech stack, existing patterns

This context reading happens once at loop start and again if you're resuming after a break.

## The loop

For each iteration:

### Pick the next issue

Find the next issue that meets ALL of these conditions:
- **Status is `Ready`**
- **All dependencies are `Done`** (check the Status of each issue listed in Dependencies)
- **Lowest ISSUE number** among eligible issues (respect the intended order)

If no issues are eligible (all remaining have unmet dependencies or are not Ready), stop and tell the user. Explain what's blocked and why.

### Transition: Ready → In Progress

Update the issue's Status in the `.issues.md` file:

```markdown
**Status:** In Progress
```

Commit this change:
```
git commit -m "issue-{N}: start — {issue title}"
```

### Implement

Now build it. Follow these principles:

**Read before you write.** Understand the existing code patterns, naming conventions, file structure. Match them. Don't introduce a new pattern unless the issue explicitly calls for it.

**Work the vertical slice.** The issue specifies which layers it touches. Implement all of them — don't leave the UI for later if the issue says `Layers: DB | Backend | Frontend`.

**Write tests alongside the code.** If the issue has business logic, the unit tests are part of the implementation, not an afterthought. Write testable code: separate pure logic from side effects, inject dependencies, keep functions focused.

**Commit often.** Make small, logical commits as you go. Each commit should compile and not break existing functionality. Use conventional commits:
- `feat(issue-{N}): add user model and migration`
- `feat(issue-{N}): implement registration endpoint`
- `test(issue-{N}): add unit tests for email validation`

**Fill the dev notes.** Update the `Dev notes` field in the issue with:
- Approach taken and why
- Any assumptions or decisions made during implementation
- Files created or modified
- Anything the reviewer should pay attention to

### Transition: In Progress → In Review

When implementation is complete:

1. Update the issue's Status in the `.issues.md`:
   ```markdown
   **Status:** In Review
   ```

2. Check the acceptance criteria checkboxes that you've satisfied:
   ```markdown
   - [x] User can register with email and password
   - [x] Unit tests pass for validation logic
   - [ ] Error messages display correctly  ← leave unchecked if not fully confident
   ```

3. Commit:
   ```
   git commit -m "issue-{N}: ready for review — {issue title}"
   ```

4. Present to the human. Give a concise summary:
   - What you built
   - Which acceptance criteria are met
   - Any decisions or assumptions to validate
   - What to test manually
   - Any open concerns

Then **stop and wait for the human's response.**

### Human review

The human will respond with one of:
- **Approval** ("looks good", "approved", "ship it", "✅", etc.)
- **Rejection with feedback** ("the validation is wrong", "change X to Y", specific issues)
- **Questions** (needs clarification before approving)

**On approval:**
1. Update Status → `Done`
2. Mark all acceptance criteria as checked: `- [x]`
3. Commit: `git commit -m "issue-{N}: done — {issue title}"`
4. Move to the next iteration of the loop

**On rejection:**
1. Keep Status as `In Review` (don't revert to Ready)
2. Read the feedback carefully
3. Append the feedback to dev notes
4. Make the requested changes
5. Commit the fixes
6. Present again for review with a summary of what changed
7. Wait for the human again

**On questions:**
1. Answer the question based on what you know
2. If you need to check the code or spec, do so and respond
3. Wait for the follow-up (which will be approval or rejection)

### Loop continuation

After an issue is Done, check for the next eligible issue and continue. If there are no more eligible issues:
- If all issues are Done → congratulate the user, the feature is complete
- If some issues are blocked → explain what's blocked and which dependencies are missing
- If some issues are still in Backlog (not Ready) → remind the user to mark them as Ready when appropriate

## State machine summary

```
Backlog → (user sets) → Ready → (loop picks up) → In Progress → (implementation done) → In Review
                                                                                           │
                                                    ┌─────────────────────────────────────┘
                                                    │
                                              Human reviews
                                                    │
                                         ┌──────────┴──────────┐
                                         ▼                     ▼
                                       Done              Fix & re-review
                                    (next issue)        (stays In Review)
```

Valid statuses: `Backlog`, `Ready`, `In Progress`, `In Review`, `Done`

## Git workflow

- **Branch**: Create a feature branch from main at loop start: `feat/{feature-name}` (e.g., `feat/tenant-invitation`)
- **Commits**: Small, frequent, conventional commits tagged with issue number
- **All status transitions** get committed to keep the `.issues.md` in sync with git history

## Principles

- **One issue at a time.** Never work on two issues in parallel. Finish one, get approval, move to the next.
- **The human is the gatekeeper.** Never mark an issue as Done without explicit human approval. This is non-negotiable.
- **The .issues.md is the source of truth.** Every status change is reflected there and committed to git.
- **Overcommunicate during review.** The human's time is expensive. Give them everything they need to review quickly: what changed, what to test, what you're unsure about.
- **Don't gold-plate.** Implement what the issue says. If you notice something that should be improved but isn't in scope, add it to dev notes as a suggestion — don't do it.
