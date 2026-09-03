# ANSI and Markdown output

## ANSI terminal

Static diagrams use SGR (`CSI ... m`) only. ANSI bytes have zero display cells. Construct and validate plain rows first, then wrap spans:

```text
ESC[36mtextESC[0m
```

Reset every styled span or at least every line. Never depend on style state leaking across rows. Exclude cursor movement, absolute positioning, erasure, OSC hyperlinks/title/clipboard, DCS, APC, terminal queries, and alternate-screen controls: they mutate terminal state and make captured output unsafe or nonportable.

Color is redundant decoration. Include text/symbol semantics such as `ACTIVE`, `WARN`, arrowheads, or border weight.

## Markdown

Raw ANSI remains literal/invisible garbage in most Markdown renderers; omit it. Use a fenced code block. Backticks inside a code block are ordinary content unless they match a closing fence. Choose a fence longer than the longest backtick run, or use tildes:

```markdown
~~~~text
`literal backtick`
~~~~
```

Do not escape ordinary box-drawing or Markdown punctuation inside the fence. Preserve spaces; avoid tabs because renderer tab stops differ.

## Plain/ASCII fallback

Map Unicode borders to `+ - |` and arrows to `< > ^ v`. Re-run layout because a Unicode arrow like `──►` and ASCII `-->` may have different cell counts. Never transliterate after final padding without revalidation.
