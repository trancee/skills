---
name: libacvp-json-kotlin
description: "Models, parses, validates, and tests libacvp and ACVP JSON artifacts in Kotlin. Use when mapping protocol envelopes, offline bundles, session files, registrations, vector sets, test groups, test cases, responses, or algorithm-specific fields to kotlinx.serialization models. Don't use for operating ACVP sessions, implementing cryptographic algorithms, parsing legacy CAVP response files, generic JSON tutorials, or claiming algorithm validation."
compatibility: "Targets cisco/libacvp 2.3.1 at commit 1877259518794f43e4e679f4c5864efa12c32e13 and ACVP protocol 1.0. Confirm current libacvp and NIST algorithm specifications before schema changes. Kotlin examples use kotlinx.serialization JSON. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://github.com/cisco/libacvp"
  sourceVersion: "cisco/libacvp@1877259518794f43e4e679f4c5864efa12c32e13; libacvp 2.3.1; ACVP protocol 1.0; inspected 2026-09-05"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-05T19:01:40+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-05T19:01:40+02:00"
---

# libacvp JSON in Kotlin

## Step 1: Identify the artifact contract

1. CLASSIFY ACVP protocol envelope | libacvp request bundle | libacvp response bundle | session-resume file | registration | bare vector set | disposition.
2. RECORD producer/version, exact algorithm/mode/revision, request versus response direction, online/offline/generic path, expected number of vector sets, and whether credentials or implementation secrets may be present.
3. READ `references/file-shapes.md` before defining the root Kotlin type. Treat libacvp repository fixtures as parser evidence; use the current NIST base and exact algorithm specification as the wire authority.
4. ROUTE ACVP source selection, validation semantics, or server operation to `nist-cavp`. ROUTE general kotlinx.serialization setup/custom serializer work to `kotlinx-serialization`.
5. STOP if the artifact provenance or request/response role is unknown; the same JSON keys have different obligations by role and algorithm revision.

Completion: one artifact kind, producer revision, algorithm tuple, direction, trust boundary, and secret-handling policy are explicit.

## Step 2: Inspect representative files without exposing values

RUN on local artifact samples:
```bash
python3 scripts/inspect-acvp-json.py path/to/file.json --json
```

1. INSPECT every distinct artifact kind and every supported `(algorithm, mode, revision, testType)` tuple.
2. COMPARE field/type fingerprints, not secret values. Keep JWT, access token, private key, seed, entropy, and implementation-output values out of logs and reports.
3. FAIL on duplicate JSON keys, invalid root shape, malformed IDs, duplicate `vsId`/`tgId`/`tcId`, missing `testGroups`/`tests`, or non-object hierarchy members.
4. COPY `assets/acvp-json-report.md`; record sample provenance/digests, shapes, dispatch keys, field ownership, unknowns, and redaction decisions.

Completion: every sample has a deterministic structural report and every reported structural error is resolved or intentionally rejected.

## Step 3: Model the root as shape-first JSON

READ `references/kotlin-modeling.md`. COPY `assets/AcvpEnvelope.kt` into the Kotlin project and adapt its package name.

1. PARSE the root once to `JsonElement`; classify object versus array before typed decoding.
2. RECOGNIZE an ACVP envelope by a leading object containing string `acvVersion`; preserve the remaining objects in order.
3. RECOGNIZE a libacvp offline/session metadata object by fields such as `url`, `jwt`, `isSample`, or `vectorSetUrls`; never deserialize `jwt` into a printable data class.
4. RECOGNIZE a vector set only when `vsId`, `algorithm`, and array `testGroups` have valid JSON types.
5. PRESERVE unclassified payload objects as `JsonObject` until their role is known; never guess from filename or array position alone.
6. USE `Long` for `vsId`, `tgId`, and `tcId`; reject fractional IDs and values outside the chosen Kotlin representation.

Completion: the root classifier distinguishes protocol envelope, libacvp bundle/session metadata, bare vector set, and unsupported shape without algorithm-field decoding.

## Step 4: Split envelope, vector, group, and case ownership

1. MODEL protocol/session metadata separately from vector data.
2. MODEL vector-set fields (`vsId`, `algorithm`, optional `mode`, optional `revision`) separately from `testGroups`.
3. MODEL `tgId` plus group discriminators/parameters separately from `tests`.
4. MODEL `tcId` plus case inputs/outputs inside the exact group type.
5. PRESERVE hierarchy and order: vector set -> group -> case. Never flatten inherited group parameters into cases on the wire model.
6. PRESERVE response IDs exactly from the request; build responses from typed request context rather than rediscovering group fields.

Completion: every field has exactly one owning level and request/response models preserve all correlation IDs.

## Step 5: Dispatch from parent context

READ `references/algorithm-dispatch.md`.

1. DISPATCH vector sets by the exact `(algorithm, mode, revision)` tuple.
2. DISPATCH groups by vector tuple plus exact `testType` and any specification-defined group discriminator.
3. DECODE cases with the serializer selected by their parent group; parent discriminators do not live inside each case.
4. REJECT unknown tuple, revision, mode, test type, or incompatible field combination. Never use one permissive universal test-case class.
5. KEEP registration capability models separate from prompt/response models even when names overlap.
6. UPDATE models only from the matching NIST algorithm specification and pinned libacvp handler source; do not borrow fields from a neighboring mode or revision.

Completion: each supported tuple reaches one serializer and every unsupported tuple fails before cryptographic execution.

## Step 6: Preserve ACVP scalar semantics

1. KEEP wire hex and bit strings as `String`; validate ASCII hex, even/declared bit length, empty-value allowance, and exact width before conversion.
2. PRESERVE leading zeroes, empty strings, case IDs, bit lengths, and request field presence. Never round bit-oriented vectors to bytes.
3. DISTINGUISH missing, explicit `null`, empty string, zero, and `false`; apply defaults only when the exact schema defines them.
4. KEEP variable-size lengths in `Long` or validated decimal wrappers when `Int` range is not guaranteed.
5. REJECT duplicate object keys before kotlinx.serialization parsing because ordinary object decoding may silently overwrite them.
6. BOUND input bytes, nesting depth, array counts, decoded binary sizes, and diagnostic output before processing untrusted artifacts.

Completion: Kotlin conversion is lossless for all accepted wire values and rejects every unsupported representation explicitly.

## Step 7: Generate response models from operation contracts

1. DEFINE response types independently for each operation/test type; output fields differ even within one algorithm.
2. COPY `vsId`, `tgId`, and `tcId` from validated request objects.
3. EMIT only fields required by the matching response schema. Preserve booleans such as `testPassed`; never encode failure as missing output unless specified.
4. MODEL nested outputs such as `resultsArray` explicitly for MCT/iterative tests.
5. CONFIGURE one strict `Json` instance for wire artifacts; disable pretty-print dependence and avoid global `ignoreUnknownKeys` at the trust boundary.
6. COMPARE emitted JSON structurally and against current specification examples; object member order is not semantic, array order is.

Completion: every request branch produces exactly one schema-valid response branch with preserved IDs and no copied secret input fields.

## Step 8: Verify parser behavior and evolution

READ `references/testing-security.md`.

1. RETAIN golden fixtures for every supported artifact shape and algorithm tuple, including a current NIST example and a pinned libacvp fixture where applicable.
2. TEST duplicate keys, wrong root, missing/wrong-type IDs, duplicate IDs, unknown tuple/test type, missing arrays, null/empty/leading-zero hex, odd/nonhex values, bit-length mismatch, extreme lengths, and sensitive-field redaction.
3. TEST decode -> typed model -> encode against exact response expectations; do not require request byte-for-byte round-trip when formatting/member order changes.
4. TEST old-reader/new-writer and new-reader/old-writer behavior for each intentionally supported revision.
5. FUZZ root classification and hierarchy validation with bounded inputs before fuzzing algorithm-specific decoders.
6. RUN the actual parser on complete offline bundles and bare generic vector sets; verify every vector/group/case count and ID.

Completion: tests prove shape classification, strict dispatch, lossless scalar handling, response conformance, bounded rejection, and redaction.

## Error Handling

- Root is an object -> accept only a validated bare vector set or named metadata/disposition shape; otherwise report unsupported root.
- Root is an array -> classify each leading header/metadata object before treating later objects as vector sets.
- Repository fixture says `acvVersion: 0.5` -> treat it as historical parser evidence, not current protocol authority.
- Unknown algorithm/revision/mode/test type -> preserve a redacted structural report and stop typed decoding.
- Duplicate JSON key -> reject before kotlinx.serialization; never keep first/last silently.
- Hex length disagrees with declared bit length -> reject or route to an explicitly bit-oriented adapter; never pad or truncate.
- JWT/token appears -> redact value from errors, logs, snapshots, and generated reports.
- libacvp handler and current NIST spec differ -> model the selected producer contract explicitly; do not merge both into a permissive schema.

## Primary sources

- libacvp: https://github.com/cisco/libacvp
- ACVP base protocol: https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html
- ACVP supported algorithm specifications: https://pages.nist.gov/ACVP/#supported
