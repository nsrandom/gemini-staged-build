#!/usr/bin/env bash
set -euo pipefail

# Branch Helper for Staged Build Plugin

cmd="${1:-status}"
feature="${2:-}"

case "$cmd" in
  ensure-branch)
    if [ -z "$feature" ]; then
      echo "Error: feature name required" >&2
      exit 1
    fi
    expected_branch="staged-build/${feature}"
    current_branch=$(git branch --show-current 2>/dev/null || echo "")
    
    if git show-ref --verify --quiet "refs/heads/${expected_branch}"; then
      if [ "$current_branch" != "$expected_branch" ]; then
        git checkout "$expected_branch"
      fi
      echo "Checked out existing branch: ${expected_branch}"
    else
      git checkout -b "$expected_branch"
      echo "Created and checked out new branch: ${expected_branch}"
    fi
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

  *)
    echo "Usage: $0 {ensure-branch <feature>|get-base|get-diff <base_commit>|clean-check}"
    exit 1
    ;;
esac
