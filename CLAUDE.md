## Language

Write everything in English: docs, comments, and code.

## Coding standards

Before you write or review code, read `CODING_STANDARDS.md`.

## Comments and docs

Answer your questions from the source code, and add docs only for what no line of code can say. Agents read docs and code alike as text, so time spent maintaining docs is wasted.

Write a comment, docstring or new Markdown file only when no code search answers the question. Keep a comment or docstring to one line, and put a longer why in an ADR.

## Checks

Before you call a change done, run the checks in `README.md`.

## Agent skills

### Issue tracker

Local Markdown in `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/`. See `docs/agents/domain.md`.
