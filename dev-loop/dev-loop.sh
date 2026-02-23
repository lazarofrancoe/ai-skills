#!/bin/bash
set -euo pipefail

# ============================================================================
# dev-loop.sh — Continuous development loop orchestrated by bash
#
# Parses a .issues.md file, finds the next Ready issue, invokes Claude Code
# to implement it, then waits for human approval before continuing.
#
# Usage:
#   ./dev-loop.sh specs/feature-name.issues.md
#
# Requirements:
#   - claude CLI installed and authenticated
#   - Python 3 (for issue parsing)
#   - git initialized repo
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISSUES_FILE="${1:-}"
FEATURE_BRANCH=""

# --- Colors -----------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# --- Helpers ----------------------------------------------------------------
info()    { echo -e "${BLUE}ℹ${NC}  $*"; }
success() { echo -e "${GREEN}✓${NC}  $*"; }
warn()    { echo -e "${YELLOW}⚠${NC}  $*"; }
error()   { echo -e "${RED}✗${NC}  $*" >&2; }

# --- Validation -------------------------------------------------------------
if [[ -z "$ISSUES_FILE" ]]; then
    error "Usage: ./dev-loop.sh <path-to-issues.md>"
    exit 1
fi

if [[ ! -f "$ISSUES_FILE" ]]; then
    error "Issues file not found: $ISSUES_FILE"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    error "claude CLI not found. Install it first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

# Derive spec file from issues file (specs/feature.issues.md → specs/feature.md)
SPEC_FILE="${ISSUES_FILE%.issues.md}.md"

# --- Issue Parser -----------------------------------------------------------
get_next_issue() {
    python3 "$SCRIPT_DIR/parse-issues.py" next "$ISSUES_FILE"
}

get_issue_detail() {
    local issue_id="$1"
    python3 "$SCRIPT_DIR/parse-issues.py" detail "$ISSUES_FILE" "$issue_id"
}

update_issue_status() {
    local issue_id="$1"
    local new_status="$2"
    python3 "$SCRIPT_DIR/parse-issues.py" update-status "$ISSUES_FILE" "$issue_id" "$new_status"
}

update_issue_dev_notes() {
    local issue_id="$1"
    local notes="$2"
    python3 "$SCRIPT_DIR/parse-issues.py" update-notes "$ISSUES_FILE" "$issue_id" "$notes"
}

get_all_issues_summary() {
    python3 "$SCRIPT_DIR/parse-issues.py" summary "$ISSUES_FILE"
}

# --- Sync Hook (optional) ---------------------------------------------------
SYNC_SCRIPT="$(dirname "$SCRIPT_DIR")/sync-to-tracker/sync-to-tracker.py"

try_sync() {
    if [[ -f ".sync-config.json" ]] && [[ -f "$SYNC_SCRIPT" ]]; then
        python3 "$SYNC_SCRIPT" "$ISSUES_FILE" 2>/dev/null || true
    fi
}

# --- Git Helpers ------------------------------------------------------------
ensure_feature_branch() {
    local feature_name
    feature_name=$(basename "$ISSUES_FILE" .issues.md)
    FEATURE_BRANCH="feat/${feature_name}"

    local current_branch
    current_branch=$(git branch --show-current)

    if [[ "$current_branch" == "$FEATURE_BRANCH" ]]; then
        info "Already on branch ${BOLD}$FEATURE_BRANCH${NC}"
    elif git show-ref --verify --quiet "refs/heads/$FEATURE_BRANCH"; then
        info "Switching to existing branch ${BOLD}$FEATURE_BRANCH${NC}"
        git checkout "$FEATURE_BRANCH"
    else
        info "Creating branch ${BOLD}$FEATURE_BRANCH${NC}"
        git checkout -b "$FEATURE_BRANCH"
    fi
}

commit_status_change() {
    local issue_id="$1"
    local status="$2"
    local title="$3"
    local status_lower
    status_lower=$(echo "$status" | tr '[:upper:]' '[:lower:]')
    git add "$ISSUES_FILE"
    git commit -m "${issue_id}: ${status_lower} — ${title}" --allow-empty
}

# --- Build implementation prompt --------------------------------------------
build_prompt() {
    local issue_id="$1"
    local issue_detail="$2"
    local spec_content=""

    if [[ -f "$SPEC_FILE" ]]; then
        spec_content=$(cat "$SPEC_FILE")
    fi

    cat <<PROMPT
You are implementing a single issue from a development backlog.

## Your task

Implement the following issue completely — all layers described, including unit tests for any business logic.

${issue_detail}

## Spec context

The parent spec for this feature:

${spec_content}

## Rules

1. Read the existing codebase first. Match conventions, patterns, naming, file structure.
2. Implement the full vertical slice: every layer listed in the issue (DB, Backend, Frontend, etc).
3. Write unit tests for business logic alongside the code — not as an afterthought.
4. Make small, logical git commits as you go. Use conventional commits prefixed with the issue id:
   - feat(${issue_id}): description
   - test(${issue_id}): description
   - fix(${issue_id}): description
5. Do NOT modify the .issues.md file — the orchestrator handles status transitions.
6. Only implement what the issue describes. If you spot something out of scope, mention it but don't do it.
7. When done, output a summary of:
   - What you built
   - Which files you created/modified
   - Which acceptance criteria you believe are met
   - Anything the reviewer should pay attention to
   - Any concerns or assumptions you made
PROMPT
}

# --- Build fix prompt -------------------------------------------------------
build_fix_prompt() {
    local issue_id="$1"
    local issue_detail="$2"
    local feedback="$3"
    local spec_content=""

    if [[ -f "$SPEC_FILE" ]]; then
        spec_content=$(cat "$SPEC_FILE")
    fi

    cat <<PROMPT
You previously implemented an issue and received feedback from the reviewer. Fix the issues described.

## The issue

${issue_detail}

## Reviewer feedback

${feedback}

## Spec context

${spec_content}

## Rules

1. Focus specifically on addressing the reviewer's feedback.
2. Make targeted fixes — don't refactor unrelated code.
3. Commit your changes with: fix(${issue_id}): description of what you fixed
4. Do NOT modify the .issues.md file.
5. When done, output a summary of what you changed and how it addresses the feedback.
PROMPT
}

# --- Main Loop ==============================================================
main() {
    echo ""
    echo -e "${BOLD}${CYAN}╔══════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║           DEV LOOP                   ║${NC}"
    echo -e "${BOLD}${CYAN}╚══════════════════════════════════════╝${NC}"
    echo ""
    info "Issues file: ${BOLD}$ISSUES_FILE${NC}"
    info "Spec file:   ${BOLD}$SPEC_FILE${NC}"
    echo ""

    ensure_feature_branch

    echo ""
    echo -e "${BOLD}Current backlog:${NC}"
    get_all_issues_summary
    echo ""

    while true; do
        # --- Find next issue ------------------------------------------------
        local next
        next=$(get_next_issue)

        if [[ "$next" == "NONE" ]]; then
            echo ""
            echo -e "${BOLD}${GREEN}═══════════════════════════════════════${NC}"

            # Check if everything is done or if things are blocked
            local summary
            summary=$(get_all_issues_summary)

            if echo "$summary" | grep -q "Backlog\|Ready\|In Progress\|In Review"; then
                warn "No eligible issues to pick up. Remaining issues may be blocked."
                echo ""
                echo "$summary"
            else
                success "All issues are Done! Feature complete. 🎉"
            fi

            echo -e "${BOLD}${GREEN}═══════════════════════════════════════${NC}"
            break
        fi

        local issue_id issue_title
        issue_id=$(echo "$next" | head -1)
        issue_title=$(echo "$next" | tail -1)

        echo ""
        echo -e "${BOLD}${CYAN}───────────────────────────────────────${NC}"
        echo -e "${BOLD}  Picking up: ${issue_id}: ${issue_title}${NC}"
        echo -e "${BOLD}${CYAN}───────────────────────────────────────${NC}"
        echo ""

        # --- Transition to In Progress --------------------------------------
        update_issue_status "$issue_id" "In Progress"
        commit_status_change "$issue_id" "start" "$issue_title"
        try_sync
        success "Status → In Progress"

        # --- Get full issue detail ------------------------------------------
        local issue_detail
        issue_detail=$(get_issue_detail "$issue_id")

        # --- Invoke Claude Code ---------------------------------------------
        info "Invoking Claude Code for implementation..."
        echo ""

        local prompt prompt_file
        prompt=$(build_prompt "$issue_id" "$issue_detail")
        prompt_file=$(mktemp /tmp/dev-loop-prompt.XXXXXX)
        printf '%s' "$prompt" > "$prompt_file"

        claude -p "$(cat "$prompt_file")" \
            --verbose \
            --allowedTools "Bash(git commit:*),Bash(git add:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Read,Write,Edit,Bash(mkdir:*),Bash(ls:*),Bash(cat:*),Bash(find:*),Bash(grep:*),Bash(npm:*),Bash(npx:*),Bash(node:*),Bash(pnpm:*),Bash(yarn:*),Bash(pip:*),Bash(python:*),Bash(pytest:*),Bash(cargo:*)"

        rm -f "$prompt_file"

        # --- Transition to In Review ----------------------------------------
        echo ""
        update_issue_status "$issue_id" "In Review"
        commit_status_change "$issue_id" "review" "$issue_title"
        try_sync
        success "Status → In Review"

        # --- Human Review Loop ----------------------------------------------
        while true; do
            echo ""
            echo -e "${BOLD}${YELLOW}┌─────────────────────────────────────┐${NC}"
            echo -e "${BOLD}${YELLOW}│         REVIEW: ${issue_id}              │${NC}"
            echo -e "${BOLD}${YELLOW}└─────────────────────────────────────┘${NC}"
            echo ""
            echo -e "  ${GREEN}a${NC} = approve    ${RED}r${NC} = reject (with feedback)    ${BLUE}d${NC} = show diff    ${CYAN}s${NC} = skip"
            echo ""
            read -rp "  → " review_choice

            case "$review_choice" in
                a|approve|yes|y|✅)
                    # --- Approved -------------------------------------------
                    update_issue_status "$issue_id" "Done"
                    commit_status_change "$issue_id" "done" "$issue_title"
                    try_sync
                    echo ""
                    success "${issue_id} → Done ✓"
                    break
                    ;;
                r|reject|no|n)
                    # --- Rejected -------------------------------------------
                    echo ""
                    echo -e "  ${YELLOW}Enter feedback (end with empty line):${NC}"
                    local feedback=""
                    while IFS= read -r line; do
                        [[ -z "$line" ]] && break
                        feedback+="$line"$'\n'
                    done

                    if [[ -z "$feedback" ]]; then
                        warn "No feedback provided. Please describe what needs to change."
                        continue
                    fi

                    info "Sending feedback to Claude Code..."
                    echo ""

                    local fix_prompt fix_prompt_file
                    fix_prompt=$(build_fix_prompt "$issue_id" "$issue_detail" "$feedback")
                    fix_prompt_file=$(mktemp /tmp/dev-loop-fix-prompt.XXXXXX)
                    printf '%s' "$fix_prompt" > "$fix_prompt_file"

                    claude -p "$(cat "$fix_prompt_file")" \
                        --verbose \
                        --allowedTools "Bash(git commit:*),Bash(git add:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Read,Write,Edit,Bash(mkdir:*),Bash(ls:*),Bash(cat:*),Bash(find:*),Bash(grep:*),Bash(npm:*),Bash(npx:*),Bash(node:*),Bash(pnpm:*),Bash(yarn:*),Bash(pip:*),Bash(python:*),Bash(pytest:*),Bash(cargo:*)"

                    rm -f "$fix_prompt_file"

                    echo ""
                    info "Fixes applied. Review again:"
                    # Loop back to review
                    ;;
                d|diff)
                    # --- Show diff ------------------------------------------
                    echo ""
                    git diff HEAD~$(git log --oneline "$FEATURE_BRANCH" --not main | wc -l)..HEAD --stat
                    echo ""
                    read -rp "  Show full diff? (y/n): " show_full
                    if [[ "$show_full" == "y" ]]; then
                        git diff HEAD~$(git log --oneline "$FEATURE_BRANCH" --not main | wc -l)..HEAD | less
                    fi
                    ;;
                s|skip)
                    # --- Skip -----------------------------------------------
                    warn "Skipping ${issue_id}. Status remains In Review."
                    update_issue_status "$issue_id" "Ready"
                    commit_status_change "$issue_id" "skipped" "$issue_title"
                    try_sync
                    break
                    ;;
                *)
                    warn "Unknown option. Use: a (approve), r (reject), d (diff), s (skip)"
                    ;;
            esac
        done
    done
}

main
