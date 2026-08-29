# NIST vector integration: [algorithm/revision/operation]

## Test identity

- **Algorithm/revision:** [exact standard and revision]
- **Mode/operation:** [encrypt, decrypt, sigGen, sigVer, component, etc.]
- **Parameters:** [key size, curve, hash/XOF, tag/output sizes, lengths]
- **Implementation/API:** [library version and exact boundary]

## Vector source

- **Track:** [static CAVP archive | ACVTS Demo | ACVTS Production]
- **Landing/specification:** [URL]
- **Direct archive or vector-set:** [URL or redacted identifier]
- **Retrieved:** [ISO 8601 timestamp]
- **SHA-256:** [archive digest, if static]
- **Files/vector sets:** [selected members or vsIds]
- **Governing procedure:** [validation-system or ACVP algorithm document]

## Coverage

| Test type/group | Direction | Parameters | Cases | Result |
| --- | --- | --- | ---: | --- |
| [KAT/AFT/MCT/etc.] | [operation] | [group context] | 0 | [pass/fail/unsupported] |

## Prerequisites

| Required algorithm | Revision/mode | Evidence/status |
| --- | --- | --- |
| [algorithm] | [revision] | [vector set/certificate/status] |

## Verification

- **Archive/syntax check:** [command and result]
- **Implementation test:** [command and result]
- **First failing case:** [archive entry + section + COUNT, or vsId/tgId/tcId]
- **Intermediate checkpoint:** [if stateful]

## Validation status

- **Regression evidence:** [what static or Demo vectors establish]
- **Formal status:** [not validated | Production session through accredited lab | certificate]
- **Limitations:** [unsupported groups, unavailable device/environment, unverified assumptions]
