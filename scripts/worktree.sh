#!/usr/bin/env bash
set -euo pipefail

from=main
case "${1:-}" in
  "") ;;
  --from) from=${2:-main} ;;
  *)
    echo "usage: scripts/worktree.sh [--from [branch=$from]]" >&2
    exit 2
    ;;
esac

cd "$(dirname "$0")"
scripts=$PWD
main_checkout=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
name=$(printf 'wt-%04x' "$RANDOM")
path=$main_checkout/.claude/worktrees/$name

git fetch -q origin "$from"
# FETCH_HEAD leaves the new branch without an upstream, so a bare `git push` cannot reach $from.
git worktree add -q -b "$name" "$path" FETCH_HEAD

# Runs this checkout's ports.sh, because $from may hold an older one.
cd "$path"
"$scripts/ports.sh"
echo "worktree: $path"
echo "branch: $name, rename it with: git branch -m new_branch_name"
