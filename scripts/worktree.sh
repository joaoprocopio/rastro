#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
main_checkout=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
name=$(printf 'wt-%04x' "$RANDOM")
path=$main_checkout/worktrees/$name

git fetch -q origin main
# FETCH_HEAD leaves the new branch without an upstream, so a bare `git push` cannot reach main.
git worktree add -q -b "$name" "$path" FETCH_HEAD

cd "$path"
scripts/ports.sh
echo "worktree: $path"
echo "branch: $name, rename it with: git branch -m new_branch_name"
