# Wycheproof integration: [algorithm or scope]

## Source

- **Repository:** `https://github.com/C2SP/wycheproof`
- **Pinned commit:** `[full commit SHA]`
- **Vector files:** `[testvectors_v1/...json]`
- **Schemas:** `[schemas/...json and dependencies]`
- **Update mechanism:** [submodule | vendored files | package]

## Implementation boundary

- **Library/version:** [implementation under test]
- **Public API:** [exact functions or methods]
- **Operations:** [encrypt/decrypt, sign/verify, derive, encap/decap, parse]
- **Supported groups:** [group types and parameter sets]
- **Unsupported groups:** [explicit limitations and rationale]

## Result policy

| Result | Required behavior | Project policy |
| --- | --- | --- |
| `valid` | Accept and return the exact expected output | [policy] |
| `invalid` | Reject without releasing unauthorized output | [accepted rejection signals] |
| `acceptable` | Apply flag-specific compatibility policy | [accept/reject by flag] |

## Coverage

| Vector file | Schema | Valid | Invalid | Acceptable accepted | Acceptable rejected | Unsupported |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `[file]` | `[schema]` | 0 | 0 | 0 | 0 | 0 |

## Verification

- **Schema validation:** `[command and result]`
- **Structural validation:** `[command and result]`
- **Implementation tests:** `[command and result]`
- **CI job:** `[workflow/job]`

## Failures

### `[file]` tcId `[id]`: [summary]

- **Group type/source:** [type, source name/version]
- **Result/flags:** [result and resolved flag descriptions]
- **Expected:** [behavior/output]
- **Observed:** [return/error/output]
- **Security impact:** [assessment or unresolved]
- **Disposition:** [fixed, accepted policy, unsupported, reported privately]
