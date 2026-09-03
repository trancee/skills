---
name: terminal-diagrams
description: "Designs, renders, and validates aligned ASCII, Unicode box-drawing, and ANSI-colored terminal diagrams. Use when translating architectures, data schemas, network topologies, process flows, dependency graphs, state machines, or aligned tables into terminal or Markdown text; calculating display-cell widths; routing labeled connectors; or repairing broken borders and ANSI padding. Don't use for pixel graphics, freehand illustrations, charts requiring quantitative axes, interactive TUIs, browser-native SVG or Canvas output, Mermaid when text art is not required, or terminal capability detection unrelated to diagram rendering."
compatibility: "Targets monospaced UTF-8 terminals and Markdown fenced code blocks. Display width depends on terminal, font, Unicode version, locale, and emoji policy; declare the width profile and avoid unsupported grapheme sequences. Validator uses a conservative Unicode 17-style cell model, accepts SGR color only, and requires Python 3.11+."
metadata:
  category: "development"
  source: "https://www.unicode.org/reports/tr11/"
  sourceVersion: "Unicode 17 UAX #11 revision 44; UAX #29 revision 47; xterm control sequences patch 411; user specification 2026-09-03"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-03T17:34:22+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-03T17:34:22+02:00"
---

# Terminal Diagrams

## Step 1: Define the rendering contract

1. IDENTIFY architecture | schema | topology | process | dependency graph | state machine | table | repair.
2. RECORD target environment (`markdown_code_block` or `ansi_terminal`), charset (`unicode` or `ascii`), maximum canvas columns, width profile, alignment, flow direction, node hierarchy, edge directions/labels, required emphasis, and whether every canvas row or only named rectangular components must share a width.
3. COPY `assets/layout-request.json` when the request is structured; validate its shape against `assets/layout-request.schema.json` before layout.
4. READ `references/width-model.md` before measuring non-ASCII labels or adding ANSI.
5. CHOOSE Mermaid/SVG instead when exact graph routing or browser-native scaling matters more than terminal fidelity; keep text diagrams for genuine terminal/Markdown output.

Completion: target, character repertoire, cell-width policy, canvas bound, components, and edge semantics are explicit.

## Step 2: Normalize the semantic graph

1. LIST nodes with stable IDs, labels, body rows, border emphasis, and optional style.
2. LIST directed, reverse, bidirectional, and undirected edges with source, target, label, and required route.
3. COLLAPSE decorative nodes that add no semantic distinction; group repeated siblings only when the grouping remains clear.
4. ORDER nodes by reading flow and dependencies. Use top-to-bottom for sequences/hierarchies and left-to-right for compact pipelines.
5. BREAK cycles with a clearly labeled return edge; never imply direction solely through placement or color.

Completion: every visible box and connector maps to one semantic node/edge, with no orphan or ambiguous direction.

## Step 3: Establish the width profile

1. MEASURE terminal display cells, not bytes, Unicode scalar count, grapheme count, or language `len`.
2. TREAT ANSI SGR sequences as zero cells; inject them only after plain layout geometry is complete.
3. TREAT box-drawing glyphs as one cell, combining marks as zero advance, and East Asian Wide/Fullwidth characters as two cells under the declared profile.
4. SET ambiguous-width policy to 1 or 2 explicitly. Avoid emoji ZWJ, flags, keycaps, variation-sensitive glyphs, tabs, and private-use symbols unless the destination terminal is known and exercised.
5. NORMALIZE line endings. Preserve label Unicode normalization unless the contract allows normalization; visually equivalent sequences can have different width behavior.

Completion: every content fragment has a deterministic visible-cell width under one declared profile.

## Step 4: Size and render nodes

READ `references/box-grammar.md`.

1. COMPUTE each content row’s visible width; choose inner width as the maximum content width plus declared left/right padding.
2. WRAP at semantic boundaries before sizing when a label exceeds the canvas. Never slice through a grapheme cluster or ANSI sequence.
3. RENDER one consistent border family per box: single, double, or raw ASCII. Match all corners, sides, dividers, and junctions.
4. PAD content rows to the inner width before styling. Apply left, right, or centered alignment from cell widths.
5. ASSERT every row in that rectangular node has identical visible width, including corners and dividers.

Completion: each node is rectangular, internally aligned, and within its allocated columns.

## Step 5: Place nodes on the canvas

READ `references/layout-strategies.md`.

1. ASSIGN non-overlapping row/column origins on a conceptual cell grid.
2. RESERVE at least one blank column/row between unrelated boxes and enough corridor space for arrows and edge labels.
3. ALIGN sibling boxes consistently by top, centerline, or column; avoid accidental near-alignment.
4. KEEP the reading order monotonic where possible. Minimize crossings before adding junction glyphs.
5. IF the canvas exceeds `max_width`, wrap labels, stack siblings, shorten nonessential labels, or split into named panels; never silently truncate semantics.

Completion: node rectangles fit the canvas and leave routable corridors without collisions.

## Step 6: Route connectors

1. ROUTE orthogonal horizontal/vertical segments through reserved corridors. Use `─`, `│`, `┌┐└┘`, `├┤┬┴┼` for Unicode or `-`, `|`, `+` for ASCII.
2. TERMINATE directed horizontal edges with `►`/`◄` and vertical edges with `▼`/`▲`; use a documented ASCII fallback such as `>`/`<`/`v`/`^`.
3. PLACE labels in a deliberate edge gap: `──[ gRPC ]──►`. Include label brackets/spaces in the route width calculation.
4. USE T-junctions/cross-junctions only when lines actually connect. For visual crossings without connection, reroute or state the convention explicitly.
5. KEEP arrowheads adjacent to the target-facing segment and never let ANSI styling separate an arrowhead from its geometry.

Completion: each edge reaches its intended ports, preserves direction/label, and crosses no node or unrelated text.

## Step 7: Render tables and schema grids

1. CALCULATE each column width from header and body cell display widths plus padding.
2. WRAP cells into physical rows before drawing horizontal separators; keep every physical table row at the same total width.
3. ALIGN text by meaning: labels left, numbers right, status consistently; do not use color as the only status signal.
4. USE matching junctions for the selected border family and include one padding cell on both sides unless the compact contract says otherwise.
5. REPEAT or omit headers only by request; split tables that cannot fit without unreadable abbreviations.

Completion: all separators meet, every column boundary is constant, and every physical row fits the canvas.

## Step 8: Apply target-specific styling

READ `references/ansi-markdown.md`.

1. FOR `markdown_code_block`, emit no raw ANSI. Wrap the plain diagram in a fence longer than any backtick run in the content, or use a tilde fence.
2. FOR `ansi_terminal`, start from verified plain geometry; wrap only text/border spans with SGR and reset each styled span/line to prevent bleed.
3. ALLOW SGR color/emphasis only. Exclude cursor movement, erasure, hyperlinks, OSC/DCS/APC strings, and terminal queries from static diagram output.
4. PRESERVE a non-color semantic cue for every emphasized state.
5. GENERATE an ASCII fallback when Unicode support is unknown or explicitly requested.

Completion: stripping SGR from terminal output yields exactly the verified plain layout; Markdown contains no escape bytes.

## Step 9: Validate and self-correct

READ `references/validation.md`.

1. SAVE the unfenced diagram to a file and run:
```bash
python3 scripts/validate-layout.py diagram.txt --target markdown_code_block --canvas-width 80 --component 1:5
```
2. FOR ANSI output, pass `--target ansi_terminal`; list every rectangular component with repeatable `--component START:END`. Use `--equal-width` only when the entire canvas is intentionally rectangular.
3. FIX the first reported line/component by recalculating visible cells and padding; rerun until exit code 0.
4. VISUALLY inspect the actual destination terminal/Markdown renderer, especially wide/ambiguous characters and labeled junctions.
5. COPY `assets/layout-report.md` for load-bearing diagrams and record width profile, component ranges, validation, and renderer limitations.

Completion: validator passes, actual rendering preserves alignment, and every semantic edge/node is present.

## Error Handling

- Borders look jagged after color -> remove ANSI, fix plain cell geometry, then reapply SGR around already-padded spans.
- Python/string lengths match but columns do not -> use display-cell width; inspect wide, combining, ambiguous, emoji, tab, and control characters.
- Validator rejects complex grapheme -> replace it with stable text/glyphs or validate with the exact destination terminal’s pinned width library/profile.
- Markdown shows color escapes -> strip ANSI and regenerate the `markdown_code_block` branch.
- Box mixes `│` with double corners -> choose one complete border family and regenerate every edge/junction.
- Edge label pushes past target -> reserve the full `[ label ]` width, shorten/wrap the label, or reroute vertically.
- Connectors cross ambiguously -> reroute; use `┼` only for a real connection and document nonconnecting crossings.
- Diagram exceeds canvas -> stack, wrap, abbreviate with a legend, or split panels; preserve semantic labels.
- Fence closes inside content -> use a longer backtick fence or tilde fence.
