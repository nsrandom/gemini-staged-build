#!/usr/bin/env bash
set -euo pipefail

# Branch Helper for Staged Build Plugin

cmd="${1:-status}"
feature="${2:-}"

case "$cmd" in
  branch-exists)
    if [ -z "$feature" ]; then
      echo "Error: feature name required" >&2
      exit 1
    fi
    if git show-ref --verify --quiet "refs/heads/${feature}"; then
      echo "EXISTS"
      exit 0
    else
      echo "NOT_FOUND"
      exit 1
    fi
    ;;

  ensure-branch)
    if [ -z "$feature" ]; then
      echo "Error: feature name required" >&2
      exit 1
    fi
    if [ "$feature" = "main" ] || [ "$feature" = "master" ]; then
      echo "Error: Cannot build directly on main or master. Specify a feature branch name." >&2
      exit 1
    fi

    expected_branch="${feature}"
    current_branch=$(git branch --show-current 2>/dev/null || echo "")
    reuse_flag="${3:-}"

    if git show-ref --verify --quiet "refs/heads/${expected_branch}"; then
      if [ "$reuse_flag" = "--reuse" ] || [ "$current_branch" = "$expected_branch" ]; then
        if [ "$current_branch" != "$expected_branch" ]; then
          git checkout "$expected_branch"
        fi
        echo "Checked out existing branch: ${expected_branch}"
      else
        echo "BRANCH_EXISTS: Branch '${expected_branch}' already exists. Ask user to confirm reuse."
        exit 2
      fi
    else
      git checkout -b "$expected_branch"
      echo "Created and checked out new branch: ${expected_branch}"
    fi
    ;;

  commit-stage)
    if [ -z "$feature" ] || [ -z "${3:-}" ] || [ -z "${4:-}" ]; then
      echo "Usage: $0 commit-stage <feature> <stage_num> <message>" >&2
      exit 1
    fi
    stage_num="$3"
    shift 3
    msg="$*"
    commit_msg="${feature}-stage-${stage_num}: ${msg}"
    git add -A
    git commit -m "$commit_msg"
    echo "Committed: $commit_msg"
    ;;

  get-base)
    git rev-parse HEAD
    ;;

  get-diff)
    base_commit="${2:-HEAD~1}"
    git diff "$base_commit"
    untracked=$(git ls-files --others --exclude-standard)
    if [ -n "$untracked" ]; then
      echo -e "\n--- Untracked Files ---"
      for f in $untracked; do
        echo "=== $f ==="
        cat "$f" 2>/dev/null || true
      done
    fi
    ;;

  clean-check)
    status_out=$(git status --porcelain -- ':!specs' 2>/dev/null || true)
    if [ -n "$status_out" ]; then
      echo "DIRTY"
      echo "$status_out"
      exit 1
    else
      echo "CLEAN"
    fi
    ;;

  ensure-gitignore)
    pattern="specs/**/scratchpad/"
    if [ -f .gitignore ]; then
      if grep -qF "$pattern" .gitignore 2>/dev/null; then
        echo "GITIGNORE_OK"
      else
        echo -e "\n# Staged Build ephemeral scratchpad\n${pattern}" >> .gitignore
        echo "GITIGNORE_UPDATED"
      fi
    else
      echo -e "# Staged Build ephemeral scratchpad\n${pattern}" > .gitignore
      echo "GITIGNORE_CREATED"
    fi
    ;;

  clean-scratchpad)
    if [ -z "$feature" ]; then
      echo "Error: feature name required" >&2
      exit 1
    fi
    scratch_dir="specs/${feature}/scratchpad"
    if [ -d "$scratch_dir" ]; then
      rm -rf "$scratch_dir"
      echo "REMOVED: ${scratch_dir}"
    else
      echo "NOT_PRESENT: ${scratch_dir}"
    fi
    ;;

  *)
    echo "Usage: $0 {branch-exists <feature>|ensure-branch <feature> [--reuse]|commit-stage <feature> <num> <msg>|get-base|get-diff <base_commit>|clean-check|ensure-gitignore|clean-scratchpad <feature>}"
    exit 1
    ;;
esac
