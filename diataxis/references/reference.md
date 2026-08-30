# Reference rules

Source: [Reference](https://diataxis.fr/reference/), [reference vs explanation](https://diataxis.fr/reference-explanation/).
Mode=cognition+application. Lookup, not reading journey.

## Contract

- neutral, terse, authoritative within explicit machinery/version scope
- structure mirrors product/API/CLI/config logical structure
- same item kind => same heading/field/table pattern
- complete facts: type, syntax, params, required/default, constraints, return/output, errors, warnings
- examples illustrate valid shape only; no lesson/task narrative
- no opinion, motive, history, tradeoff, persuasion; move to explanation
- no goal procedure; move to how-to
- generated source acceptable only after missing semantics/errors/defaults checked
- human output: plain factual natural English

## Patterns

API item: signature -> description -> params -> returns -> throws -> example.
CLI item: syntax -> args -> options/defaults -> output/errors -> example.
Config item: key -> type -> required/default -> constraint -> effect -> example.

## Verification

Compare every documented item+field against current machinery/version. Test examples. Check sibling consistency and links.

## Reject

missing param/return/error/default; creative pattern variance; product structure mismatch; embedded tutorial/explanation; unsupported claims.
