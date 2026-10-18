# Issue tracker: local Markdown

- **Spec**: `.scratch/<feature-slug>/spec.md`.
- **Ticket**: `.scratch/<feature-slug>/issues/NN-<slug>.md`, numbered from `01`, one file per ticket.
- **Label**: the `Status:` line of the ticket.
- **Comment**: append it under `## Comments`, at the end of the ticket.

## Wayfinding operations

- **Map**: `.scratch/<effort>/map.md`.
- **Child ticket**: `.scratch/<effort>/issues/NN-<slug>.md`, with a `Type:` line in place of the `wayfinder:<type>` label.
- **Blocking**: a `Blocked by: NN, NN` line.
- **Claim**: set `Status: claimed`.
- **Resolve**: append the answer under `## Answer`, and set `Status: resolved`.
