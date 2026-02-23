# AI Skills

Claude Code skills and tools for product development workflows.

## Skills

| Skill | Description |
|-------|-------------|
| [`idea-to-spec`](./idea-to-spec/) | Transforms a raw product idea into a structured spec saved to the repo |
| [`spec-to-issues`](./spec-to-issues/) | Breaks down an approved spec into atomic, implementable issues for a kanban board |

## Tools

| Tool | Description |
|------|-------------|
| [`dev-loop`](./dev-loop/) | Bash script that orchestrates Claude Code CLI to implement issues one by one with human review |

## Usage

**Skills** go into your project's `.claude/skills/` directory:

```bash
cp -r idea-to-spec spec-to-issues /path/to/your-project/.claude/skills/
```

**dev-loop** runs from anywhere — just point it at an issues file:

```bash
./dev-loop/dev-loop.sh specs/my-feature.issues.md
```

### Workflow

```
/idea-to-spec  →  specs/feature.md
                        ↓
/spec-to-issues  →  specs/feature.issues.md
                        ↓
dev-loop.sh  →  implements issues one by one with human review
```

Each piece is independent and tracker-agnostic. State lives in the repo as markdown files.
