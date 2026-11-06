## Language

Write everything in English: docs, comments, and code.

## Coding standards

Before you write or review code, read `CODING_STANDARDS.md`.

## Comments and docs

Answer your questions from the source code, and add docs only for what no line of code can say. Agents read docs and code alike as text, so time spent maintaining docs is wasted.

Write a comment, docstring or new Markdown file only when no code search answers the question. Keep a comment or docstring to one line, and put a longer why in an ADR.

## Checks

Before you call a change done, run the checks in `README.md`.

Before you change a tracked file, create a worktree with `scripts/worktree.sh [--from branch]`, because parallel sessions share the main checkout. It starts from `main` by default and gives the worktree its own stack ports. Then give its branch the real name with `git branch -m`. In a worktree you created another way, run `scripts/ports.sh` before you start the stack.

After the checks over the whole branch diff pass, before the push, remove the stack of your worktree, as "Run a second stack beside another worktree's" in `README.md` shows. Start it again if the pipeline or a later review needs it.

When you start, commit the spec and tickets in `.scratch/`, push, and open a PR to `main`. Push again only after the code review: run the checks over the whole branch diff, push, and wait for the PR pipeline. With several tickets, only the integration branch has a PR.

## Commits

Write every commit subject as a Conventional Commit, with `!` on a breaking change: `feat!: run tasks on Procrastinate`.

## Telemetry

Traces, logs, and metrics of the `rastro` and `rastro-worker` services sit in the ClickHouse of the compose stack, behind Grafana. Read them with `docker compose exec clickhouse clickhouse-client --user clickhouse --password clickhouse`.

## GitHub

Pull requests, check runs, and reviews through `gh`. See `docs/agents/github.md`.

## Agent skills

### Issue tracker

Local Markdown in `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.
