# Wycheproof vector format

Read this reference when selecting, parsing, or auditing vector files. Treat the current file's declared JSON schema under `schemas/` as the source of truth. The repository states that legacy documents under `doc/` are not necessarily synchronized with current vectors.

## Corpus layout

Current vectors live under `testvectors_v1/`. The former `testvectors/` corpus was removed; legacy v0 data remains available from the `wycheproof-v0-vectors` tag. Do not mix v0 and v1 assumptions in one loader.

Each vector file declares a `schema` filename. Load that exact schema from the same pinned Wycheproof revision. Schema names can change when formats change; reject an unknown schema instead of guessing from `algorithm` or a filename.

## Root, group, and case hierarchy

Current vector files generally contain:

- `algorithm`: descriptive primitive name;
- `schema`: governing schema filename;
- `header`: file-level interpretation notes;
- `notes`: definitions for case flags;
- `numberOfTests`: expected total case count;
- `testGroups`: groups sharing parameters and a test `type`.

Each group supplies algorithm-specific shared inputs and a `tests` array. Current schemas commonly include a group `source` with `name` and `version`; the older root `generatorVersion` property is deprecated in current schemas.

Each test case contains:

- `tcId`: case identifier within the file;
- `comment`: case description;
- `flags`: names resolved through root `notes`;
- `result`: `valid`, `invalid`, or `acceptable`;
- algorithm-specific inputs and expected outputs.

Read group-level fields before cases. Do not flatten groups or assume fields from one schema exist in another.

## Result semantics

Apply the vector file's header, its schema, flags, and the tested operation together.

- `valid`: require acceptance and the specified correct output or behavior.
- `invalid`: require rejection of the invalid input or operation. Ensure authenticated decryption and key-validation adapters do not release output before reporting rejection.
- `acceptable`: resolve the case's flags through `notes` and apply an explicit compatibility/security policy. Acceptance or rejection may both be permitted for legacy encodings, weak parameters, or defined edge behavior. If accepted, require the specified output and all protocol safety conditions.

Never skip `acceptable` silently and never count it automatically as `valid`. Report accepted and rejected acceptable cases separately with their flags.

## Encodings

Consult the declared schema for every field. Common conventions include:

- `HexBytes`: bytes encoded as an even-length hexadecimal string;
- `BigInt`: signed two's-complement, big-endian hexadecimal with width significant to the encoding;
- `Asn`: hexadecimal bytes that may intentionally contain malformed ASN.1;
- `Der`: valid DER bytes encoded as hexadecimal;
- `Pem`: a PEM string.

Preserve leading zeroes, signed integer semantics, malformed encodings, empty byte strings, and group-declared lengths. Avoid normalizing inputs before the implementation under test sees them; normalization can erase the condition a vector is designed to exercise.

## Schema verification

For a clone of the current Wycheproof repository, prefer its maintained tooling:

```bash
GOEXPERIMENT=jsonv2 go run ./tools/vectorgen fmt --check 'testvectors_v1/*.json'
GOEXPERIMENT=jsonv2 go run ./tools/vectorgen lint
```

The current contributor guide requires Go 1.26+ and `GOEXPERIMENT=jsonv2` until Go 1.27. Re-check `doc/vectorgen.md` at the pinned revision before running these commands.

For a vendored subset, validate each file against the exact declared schema and its transitive schema references. Run `scripts/check-vectors.py` for duplicate-key, count, ID, result, and flag checks; that script is a structural supplement, not a replacement for JSON Schema validation.
