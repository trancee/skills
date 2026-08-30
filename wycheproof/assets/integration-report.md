# Wycheproof: [algorithm/scope]

## Source
- repo/commit:
- vectors/schemas:
- update: [submodule|vendor|package]

## Boundary
- library/version/API:
- operations/params/groups:
- unsupported+reason:

## Policy
| result | required | project policy |
|---|---|---|
| valid | accept+exact output | |
| invalid | reject; no unauthorized output | |
| acceptable | flag policy | |

## Coverage
| file | schema | valid | invalid | acceptable+ | acceptable- | unsupported |
|---|---|---:|---:|---:|---:|---:|
| | | 0 | 0 | 0 | 0 | 0 |

## Proof
- schema/structural/tests/CI:

## Failure: `[file]` tcId `[id]`
- group source; result/flags:
- expected/observed:
- security/disposition:
