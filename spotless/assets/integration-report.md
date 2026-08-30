# Spotless: [scope]

## Runtime and versions
- build tool/wrapper/JRE:
- Spotless plugin:
- formatter engines/versions/configs:

## Contract
- modules/formats:
- targets:
- exclusions+rationale:
- ordered FormatterSteps:
- line endings/encoding:
- rollout/ratchet ref:

## Enforcement
- local check/apply:
- CI command/lifecycle binding:
- skips/suppressions/exceptions:

## Proof
| scenario | expected | observed |
|---|---|---|
| seeded owned-file violation | check fails on file | |
| first apply | intended diff only | |
| second apply | no new diff | |
| excluded file | unchanged | |
| CI-equivalent check | passes | |

## Limitations
- unformatted scope/reason:
