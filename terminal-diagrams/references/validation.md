# Validation protocol

The validator checks:
- UTF-8 text and line endings
- terminal display-cell width under a declared ambiguous-width policy
- tabs, controls, unpaired combining marks, private-use characters, and unstable emoji/grapheme sequences
- ANSI policy: none for Markdown; SGR-only and reset-safe for terminal
- maximum canvas width
- equal widths for repeatable `--component START:END` ranges
- optional equal width for every row
- obvious single/double/ASCII corner pairing on box boundary rows

Examples:

```bash
python3 scripts/validate-layout.py diagram.txt \
  --target markdown_code_block \
  --canvas-width 80 \
  --component 1:5 \
  --component 8:12

python3 scripts/validate-layout.py colored.txt \
  --target ansi_terminal \
  --ambiguous-width 1 \
  --equal-width \
  --json
```

Component ranges refer to unfenced input lines, inclusive and 1-based. Empty separator lines within a component count as width 0 and therefore fail unless padded intentionally; normally keep separators outside ranges.

Exit codes: 0 valid, 1 validation errors, 2 invalid CLI/input. JSON output contains line widths, errors, warnings, and component results.

Passing the conservative validator is not proof for every terminal. Exercise the actual renderer when labels include non-ASCII text, the terminal uses a different Unicode width table, or fonts/locale resolve ambiguous characters differently.
