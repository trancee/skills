# Terminal cell-width model

Alignment uses terminal display cells:

`padding = intended_cells - visible_cells(content)`

Compute geometry on plain text. ANSI control sequences contribute zero cells; byte length, Unicode code-point count, and grapheme-cluster count are not cell width.

Default conservative profile:
- ASCII and Unicode box-drawing: 1 cell
- combining marks, variation selectors, zero-width format characters: 0 additional cells
- East Asian Width `W`/`F`: 2 cells
- East Asian Width `A`: declared `ambiguous_width` (normally 1 outside East Asian legacy contexts)
- C0/C1 controls and tabs: reject in diagram rows

Unicode UAX #11 explicitly warns that East_Asian_Width is not an off-the-shelf terminal-width algorithm. Actual width depends on terminal, font, locale, Unicode tables, emoji presentation, and tailoring. UAX #29 defines grapheme clusters, which may contain several code points but still do not alone determine terminal cells.

Source baseline: [UAX #11 rev 46](https://www.unicode.org/reports/tr11/tr11-46.html) and [UAX #29 rev 49](https://www.unicode.org/reports/tr29/tr29-49.html), Unicode 18. UAX #11 changes unassigned CJK ranges; UAX #29 changes Indic GB9c boundaries. Recheck Unicode tables and segmentation when introducing new characters/Indic clusters; neither revision supplies terminal cell widths.

Validator data = the running Python's `unicodedata`, plus conservative overrides. Record `unicodedata.unidata_version`; no bundled Unicode 18 table or complete UAX #29 implementation. A newer reference baseline is not a validator-conformance claim.

The bundled validator rejects width-unstable complex sequences: ZWJ emoji, regional-indicator flags, keycap sequences, private-use characters, and unpaired combining marks. Replace them with stable text or validate with the exact destination renderer and a pinned `wcwidth`/grapheme profile.

Do not normalize arbitrary labels silently. NFC may improve consistency but can change byte identity and width-table behavior. Normalize only under an explicit contract.

Centering odd slack is deterministic: put `floor(slack/2)` cells left and the remainder right, unless the request specifies the opposite bias.
