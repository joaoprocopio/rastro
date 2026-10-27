# Issue tracker: local Markdown

- **Spec**: `.scratch/<feature-slug>/spec.md`.
- **Ticket**: `.scratch/<feature-slug>/issues/NN-<slug>.md`, numbered from `01`, one file per ticket.
- **Label**: the `Status:` line of the ticket.
- **Comment**: append it under `## Comments`, at the end of the ticket.
- **Resolve**: the implementer sets `Status: resolved` in the last commit of its ticket, so the status merges with the code.
- **Close**: work ends when its PR to `main` is open. Open it with `gh pr create`, title it as a Conventional Commit (`refactor!: ...`), because the squash merge puts the title on `main`, and write the body with the `/pr` skill.

## Wayfinding operations

- **Map**: `.scratch/<effort>/map.md`.
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, with a `Type:` line in place of the `wayfinder:<type>` label.
- **Blocking**: a `Blocked by: NN, NN` line.
- **Claim**: set `Status: claimed`.
- **Resolve**: append the answer under `## Answer`, and set `Status: resolved`.
