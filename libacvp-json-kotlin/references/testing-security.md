# Testing, limits, and secret handling

## Fixture matrix

Retain at least one accepted and rejected fixture for each supported cell:

| Axis | Cases |
| --- | --- |
| Root | protocol envelope, libacvp bundle, bare vector set, unsupported object/array |
| Role | registration, prompt, response, session metadata, disposition |
| Tuple | every algorithm × mode × revision |
| Test type | every supported group branch |
| Scalar | missing, null, empty, zero, false, leading-zero hex, max length |
| Structure | missing/wrong-type arrays, duplicate IDs, duplicate keys, extra objects |
| Evolution | oldest supported and current producer revision |
| Security | JWT/token/private material redaction and bounded malformed input |

Pin every external fixture to a commit/spec revision and record its expected role. Historical libacvp fixtures with `acvVersion: 0.5` are valid only as historical/unit-test inputs.

## Duplicate keys

JSON permits interoperable parsers to disagree about duplicate member handling. Reject duplicates during tokenization, before constructing `JsonObject` or generated Kotlin models.

The bundled `scripts/inspect-acvp-json.py` uses Python's `object_pairs_hook` to detect duplicates. In Kotlin, choose or wrap a streaming/token parser that exposes object member events, or run a deterministic duplicate-key preflight before kotlinx.serialization. Test duplicates at header, vector, group, case, and nested result levels.

## Structural invariants

Require:

- Root is an object or array of objects for supported artifacts.
- Protocol header `acvVersion` is a string.
- Vector `vsId` is a nonnegative integer and unique in a bundle.
- Vector `algorithm` is a nonempty string.
- Vector `testGroups` is an array.
- Group `tgId` is a nonnegative integer and unique within its vector.
- Group `tests` is an array.
- Case `tcId` is a nonnegative integer and unique throughout its vector.
- Parent dispatch fields are present with exact types before case decoding.

Do not require `mode` for algorithms that omit it or assume `revision` from a different producer. Put those rules in the tuple-specific codec.

## Resource limits

Set limits before allocation:

- Input bytes per file/request.
- JSON nesting depth.
- Objects and members.
- Vector sets, groups, and cases.
- String/hex length and decoded bytes.
- MCT result counts and LDT/generated-message length.
- Diagnostic issue count and field fingerprint cardinality.

Reject limit excess with path and limit name, never with the raw value. Stream large artifacts if full-tree memory is not acceptable; still preserve parent context required for dispatch.

## Secret handling

Potentially sensitive fields include `jwt`, bearer/access tokens, client credentials, private keys, entropy inputs, DRBG internal values, signing seeds/randomizers, shared secrets, and plaintext depending on the test environment.

- Keep raw artifacts out of ordinary logs and exception messages.
- Report paths, keys, JSON types, lengths, and hashes only when policy permits.
- Redact values before snapshots and bug reports.
- Store session/offline files with restrictive permissions and defined deletion.
- Never place credentials in source fixtures.
- Configure kotlinx.serialization exception reporting so input payload text is not exposed.

## Behavioral tests

High-value tests:

1. Classifier selects the right root kind without inspecting secret values.
2. Unknown vector tuple stops before case decoding.
3. Parent group selects the correct case serializer.
4. Request IDs survive response generation exactly.
5. Hex validation preserves empty/leading-zero strings and rejects invalid width/chars.
6. Missing and explicit null produce different outcomes where the schema requires it.
7. Authenticated decrypt failure emits `testPassed: false` without plaintext.
8. MCT response preserves `resultsArray` order/count.
9. Complete libacvp offline bundle processes all vector sets after metadata.
10. Diagnostics and generated report never contain known sentinel secret values.

Round-trip alone is insufficient: a wrong symmetric model can encode and decode itself. Assert accepted external fixtures and exact structural response goldens.

## Fuzzing

Fuzz in layers:

1. Duplicate-key preflight and JSON tokenizer.
2. Root classifier.
3. Envelope/bundle hierarchy validator.
4. Tuple/group dispatcher.
5. Algorithm-specific scalar and response models.

Use bounded inputs and assert no crash, hang, unbounded allocation, secret echo, or accidental acceptance. Preserve minimized failures as regression fixtures with nonsecret synthetic values.
