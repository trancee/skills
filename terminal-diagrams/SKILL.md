---
name: terminal-diagrams
description: "Renders and validates ASCII/Unicode/ANSI terminal diagrams. Use for text architectures, schemas, topology, flow/state/dependency graphs, aligned tables, display-cell widths, connectors, or broken borders. Don't use for pixel graphics, quantitative charts, interactive TUIs, browser SVG/Canvas, or Mermaid when text art is not required."
compatibility: "Monospaced UTF-8 terminals/Markdown. Declare terminal/font/locale/Unicode/emoji width policy. Python 3.11+ validator uses runtime unicodedata plus conservative overrides, not full Unicode segmentation; accepts SGR only."
metadata:
  category: "development"
  source: "https://www.unicode.org/reports/tr11/"
  sourceVersion: "Unicode 18 UAX #11 revision 46 and UAX #29 revision 49; xterm patch 411; checked 2026-10-06; user specification 2026-09-03"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-03T17:34:22+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-06T15:15:21+02:00"
---

# Terminal diagrams

## 1. Contract and semantic graph

1. RECORD architecture/schema/topology/process/dependency/state/table/repair scope, target (`markdown_code_block` | `ansi_terminal`), charset, max columns, width policy, alignment/flow/hierarchy/emphasis, and rectangular component boundaries.
2. STRUCTURED request -> COPY `assets/layout-request.json`; validate against `assets/layout-request.schema.json`.
3. LIST stable node IDs, labels/body/border/style and edge direction/label/route. Collapse only decorative distinctions.
4. ORDER by reading flow/dependencies; top-down for long sequences, left-right for compact pipelines. Label return edges for cycles; placement/color alone cannot imply direction.
5. CHOOSE Mermaid/SVG if browser scaling/exact graph routing is required instead of terminal text.

Gate: each box/edge maps to semantics; no orphan or ambiguous direction.

## 2. Width

READ `references/width-model.md` for non-ASCII or ANSI.

1. MEASURE display cells, not bytes/code points/grapheme count. ANSI SGR = zero cells; apply only after geometry.
2. DECLARE ambiguous width 1/2 and renderer Unicode tables; Wide/Fullwidth = 2, supported box glyphs = 1, combining advance = 0 under the chosen profile.
3. AVOID unstable ZWJ/flags/keycaps/variation/private-use glyphs and tabs unless the destination profile is pinned and exercised.
4. NORMALIZE line endings; change label Unicode normalization only by explicit contract.
5. CHECK runtime table version. Unicode 18 references do not upgrade Python's `unicodedata` or establish terminal/UAX conformance.

Gate: deterministic measured fragments under one documented renderer policy.

## 3. Nodes and canvas

READ `references/box-grammar.md`; placement branch -> READ `references/layout-strategies.md`; examples -> READ `references/examples.md`.

1. WRAP semantic labels before sizing; never cut grapheme/ANSI sequences.
2. SET inner width = max visible content + declared padding; one complete single/double/ASCII border family per box.
3. PAD then style; left/right/center by cells. ASSERT equal visible width for every row including dividers/corners.
4. ASSIGN non-overlapping origins; reserve blank separation and corridors for arrows/labels. Align siblings intentionally.
5. REDUCE crossings. Width overflow -> wrap/stack/split named panels or shorten nonessential labels; preserve semantics, never truncate silently.

Gate: rectangular nodes fit canvas, leave corridors, and avoid collisions.

## 4. Connectors and tables

1. ROUTE orthogonal segments; Unicode `─│┌┐└┘├┤┬┴┼` or ASCII `-|+`.
2. END directed edges with `►◄▼▲` or documented `><v^` fallback; preserve bidirectional/undirected meaning.
3. RESERVE full label width, e.g. `──[ gRPC ]──►`. Keep arrowhead at target-facing segment.
4. JOIN only real connections at T/cross-junctions; reroute visual crossings or declare a nonjoining convention. Never cross node/text.
5. TABLE branch: size header/body columns by display cells + padding, wrap into physical rows, preserve constant boundaries/separator junctions. Text left, numbers right, statuses consistent; color not sole signal. Headers repeat/omit only as requested.

Gate: every edge reaches correct ports/direction/label; physical table rows align and fit.

## 5. Target styling

READ `references/ansi-markdown.md`.

- Markdown -> no ANSI; fence longer than internal backtick runs or use tildes; preserve spaces.
- ANSI -> verified plain geometry first; SGR spans reset each span/line; strip SGR to recover exactly the plain layout.
- Static output -> exclude cursor/erase/OSC/DCS/APC/query controls.
- Unknown/requested repertoire -> ASCII fallback, relayout and revalidate.
- Emphasis -> redundant text/symbol cue, not color alone.

Gate: capture-safe styling; Markdown has no escape bytes.

## 6. Validate and deliver

READ `references/validation.md`. Resolve `scripts/` from the skill package; input file is unfenced:

```bash
python3 scripts/validate-layout.py diagram.txt --target markdown_code_block --canvas-width 80 --component 1:5
```

1. DECLARE each rectangular range with repeatable `--component START:END`; `--equal-width` only for intentionally rectangular whole canvas.
2. ANSI -> `--target ansi_terminal`; explicit `--ambiguous-width`.
3. FIX first diagnostic by recomputing cells/padding; repeat to exit 0.
4. INSPECT actual destination rendering, especially non-ASCII, ambiguous glyphs and junctions.
5. LOAD-BEARING output -> COPY `assets/layout-report.md`; record policy, ranges, proof and renderer limits.

Gate: validator and actual renderer preserve geometry; every semantic node/edge present.

## Failure routing

- Color breaks borders -> fix plain cells first, then SGR.
- String lengths agree but columns differ -> width profile; inspect wide/combining/emoji/tab/control glyphs.
- Complex grapheme rejected -> stable label or exact renderer/pinned segmentation profile.
- Mixed border families -> regenerate one complete family.
- Label collision -> reserve full width, wrap/shorten label or reroute.
- Ambiguous crossing -> reroute; junction only for connection.
- Too wide -> stack/wrap/legend/named panels without losing semantics.
- Premature fence closure -> longer backtick/tilde fence.
