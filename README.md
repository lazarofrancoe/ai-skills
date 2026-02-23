# AI Skills

Claude Code skills for product development workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [`idea-to-spec`](./idea-to-spec/) | Transforms a raw product idea into a structured spec saved to the repo |
| [`spec-to-issues`](./spec-to-issues/) | Breaks down an approved spec into atomic, implementable issues for a kanban board |
| [`dev-loop`](./dev-loop/) | Continuous dev loop: picks issues, implements, waits for human review, repeats |

## Usage

Copy the skill folders you need into your project's `.claude/skills/` directory:

```bash
cp -r idea-to-spec spec-to-issues dev-loop /path/to/your-project/.claude/skills/
```

### Workflow

```
/idea-to-spec  →  specs/feature.md
                        ↓
/spec-to-issues  →  specs/feature.issues.md
                        ↓
/dev-loop  →  implements issues one by one with human review
```

Each skill is independent and tracker-agnostic. State lives in the repo as markdown files.
