# Design

Each `.excalidraw` file is a rough visual guide for building the UI, not a pixel-perfect spec. `index.excalidraw` holds the current screens, and a `proposta-*.excalidraw` file holds a redesign the user has not approved yet.

## Inspiration

Our references are Linear, Notion, and Apple. Before you design a screen, read the screenshots in `references/` and invoke the `apple-design` skill.

- From Linear, take the behavior and the details: pill filters under the header, list-detail split for records, icon actions on the right of the header, two-level filter menus, context menus with shortcuts, status chips, and dense lists with no table header.
- From Notion, take the layout, the sizes, and the proportions: a flush sidebar with square edges and a gray background, a 240 px sidebar, 30 px rows, 14 px body text, and centered pages with a reading width for documents.
- From Apple, take the principles: hierarchy through gray tones, specific labels, wayfinding, and feedback before the user hits a wall.
- When Linear and Notion disagree, use Notion's layout and Linear's behavior.
- When a screen has no reference, find the closest screen in Linear or Notion, name it in a red note, and draw from it.

## Drawing

- Draw with basic Excalidraw tools only: rectangles, ellipses, lines, arrows, and text.
- Pick colors from the default Excalidraw palette only.
- Draw icons as Unicode symbols or emoji, such as `›`, `«`, `⋯`, `👁`, and `🔔`.
- Write the final pt-BR UI copy, so the text in the design becomes the text in the code.

## Colors

Each color has one meaning:

- **Blue** (`#1971c2`): primary actions and links.
- **Green** (`#2f9e44` text on `#ebfbee`): positive status.
- **Red** (`#e03131`): annotations and errors.
- **Gray**: hierarchy, in layered tones like Apple's interfaces:
  - `#1e1e1e`: primary text.
  - `#343a40`: body text and icons.
  - `#868e96`: secondary text and placeholders.
  - `#ced4da`: input borders and disabled controls.
  - `#e9ecef`: dividers, chips, selected rows, and skeletons.
  - `#f8f9fa`: grouped backgrounds, such as the sidebar.

## Layout

- Draw every screen in a 2000×1422 frame, so all screens share one scale.
- Give each flow its own row, with its screens side by side from left to right.
- Put a red title above each frame with the screen or step name, such as "2. Verificar código".
- Draw a repeated component (sidebar, input, button) with the same size and position on every screen, so it maps to one reusable component in the code.
- Draw the states that change the code (empty, loading, error) as extra frames in a row below the main screen.

## Annotations

- Draw navigation as red arrows, each with a short label for the action that triggers it, such as "clique na linha".
- Write behavior notes as red text beside the element, such as "expira em 10 min".
- When a screen copies another product, name it in the title, such as "Menu ⋯ (referência: Notion)".

## Verification

After you edit an `.excalidraw` file, render it with `excalidraw render <file> --out /tmp/design.png` and inspect the PNG before you report done.
