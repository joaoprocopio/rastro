# Issue tracker: local Markdown

- **Spec**: `.scratch/<feature-slug>/spec.md`.
- **Ticket**: `.scratch/<feature-slug>/issues/NN-<slug>.md`, numbered from `01`, one file per ticket.
- **Label**: the `Status:` line of the ticket.
- **Comment**: append it under `## Comments`, at the end of the ticket.
- **Resolve**: the implementer sets `Status: resolved` in the last commit of its ticket, so the status merges with the code.
- **Acceptance criterion**: the agent that verifies a criterion ticks its checkbox, so an empty checkbox marks a criterion that nobody verified.
- **Close**: work ends when its PR to `main` is open, as `docs/agents/github.md` describes.
- **Review**: the maintainer reviews on the PR.
- **Review ledger**: `/pr-review` records each finding and its verdict in `.scratch/<feature-slug>/review-ledger.md`, which stays in git with the spec.

## Wayfinding operations

- **Map**: `.scratch/<effort>/map.md`.
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, with a `Type:` line in place of the `wayfinder:<type>` label.
- **Blocking**: a `Blocked by: NN, NN` line.
- **Claim**: set `Status: claimed`.
- **Resolve**: append the answer under `## Answer`, and set `Status: resolved`.
