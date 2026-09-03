# Box and junction grammar

## Single Unicode

`┌ ┐ └ ┘ ─ │ ┬ ┴ ├ ┤ ┼`

## Double Unicode

`╔ ╗ ╚ ╝ ═ ║ ╦ ╩ ╠ ╣ ╬`

## ASCII fallback

`+ + + + - | + + + + +`

Use one family inside a rectangular box. Mixed single/double junctions exist in Unicode, but introduce them only where a deliberate single/double boundary meets; otherwise mixed borders look accidental.

For inner width `W` and one-cell horizontal padding:
- outer width = `W + 2` side cells
- top = left corner + horizontal repeated `W` + right corner
- content = vertical + content padded to `W` + vertical
- divider = left junction + horizontal repeated `W` + right junction

Measure repeat counts in cells. Box glyphs are one cell under the supported profile.

Ports should land on a side glyph or junction, never a corner unless the route explicitly uses that corner. Replace the touched side glyph with the correct T-junction when a connector joins. A crossing uses `┼`/`╬` only when all segments are connected; otherwise reroute.

High emphasis may use double borders, but color/border weight must not be the only semantic cue. Add a status word, label, or legend.
