# GitHub

Use `gh` for pull requests, check runs, and reviews, and local `git` for branches and commits.

Read anything whenever the task needs it, and create or update PRs and comments without asking. Before you approve, request changes on, merge, or close a PR, delete a branch, or start a workflow, show the user the command and run it once the user approves.

## Pull requests

- **Create**: `gh pr create --base main --title "..." --body-file /tmp/pr-body.md`. Title it as a Conventional Commit (`refactor!: ...`), because the squash merge puts the title on `main`, and write the body with the `/pr` skill.
- **Read a review**: `gh api repos/{owner}/{repo}/pulls/<n>/comments` lists the comments on lines of code, because `gh pr view --comments` shows only the conversation.
- **Answer a review**: `gh api repos/{owner}/{repo}/pulls/<n>/comments/<comment_id>/replies -f body="..."`.

## Checks

- **Wait for the checks**: `gh pr checks <n> --watch`.
- **Find why a check failed**: `gh run view <run_id> --log-failed`.
- **Leave `[skip ci]` out of every commit message**: the squash merge copies each commit message into the commit on `main`, so one `[skip ci]` skips the checks of `main`.
