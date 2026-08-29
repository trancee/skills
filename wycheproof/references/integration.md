# Wycheproof integration workflow

Read this reference when mapping vector groups to a cryptographic API or maintaining a vendored corpus.

## Pin the source

Use a pinned Wycheproof commit or release. Prefer one of:

- a Git submodule pinned by the parent repository;
- vendored vector and schema files with the upstream commit recorded;
- ecosystem packaging that preserves the exact vector/schema revision.

Record the upstream repository, commit, selected vector filenames, schema filenames, and retrieval/update mechanism. Update deliberately; test IDs and schemas can change between vector versions.

Keep each selected vector file with its exact schema and referenced schema dependencies. Validate the pinned corpus before debugging the cryptographic implementation.

## Select vectors by capability

Start from the implementation's real public API:

1. Identify the primitive, operation, parameter sets, encodings, and supported sizes.
2. Inspect `testvectors_v1/` at the pinned revision for matching files.
3. Read each file's `algorithm`, `schema`, `header`, groups, and sources.
4. Include every group the public API claims to support.
5. List unsupported groups explicitly with the API limitation; do not silently filter them.

Avoid static algorithm catalogs in integration code. Discover exact filenames and group types from the pinned corpus and declared schemas.

## Build one adapter per operation

Map a vector group to the same public boundary callers use. Keep parsing separate from the cryptographic adapter.

The adapter must distinguish:

- key or parameter parsing;
- primitive execution;
- verification or authentication result;
- expected output comparison;
- unsupported capability;
- unexpected internal error.

Do not catch every exception and translate it into “rejected.” A crash, resource failure, or adapter bug is not successful invalid-input handling. Accept only documented rejection results from the tested API.

For algorithms with several encodings, pass the vector's raw encoding to the relevant parser. Do not decode ASN.1, DER, PEM, JWK, ciphertext, signature, or key material into a cleaner form before testing a parser that is part of the public boundary.

## Assert behavior

Apply `valid`, `invalid`, and `acceptable` according to `references/vector-format.md`.

For valid cases, require both acceptance and exact output. For invalid cases, require explicit rejection and no unauthorized plaintext, shared secret, key, or verified result. For acceptable cases, implement a named policy based on flags and report whether each case was accepted or rejected.

Exercise every applicable direction. For AEAD, verify encryption output and decryption/authentication behavior when the API exposes both. For signatures, test the exact signature and key encoding named by the file. For key exchange, compare the complete shared secret and apply the API's defined invalid-key behavior. For KEMs, distinguish key generation, encapsulation, decapsulation, and invalid-ciphertext behavior by group type.

## Produce actionable failures

Include these fields in every failure:

- pinned Wycheproof commit;
- vector filename and declared schema;
- algorithm and group type;
- group source name/version when present;
- `tcId`, result, flags, and comment;
- expected behavior or output;
- observed return value, error class, or output.

Resolve flags through the root `notes` map in diagnostic output. The flag describes why a case exists; it does not prove the root cause of a failure.

## Integrate into CI

Run the complete selected corpus in a deterministic test job. A fast subset may run earlier only when the complete applicable corpus remains in CI. Pin corpus updates so upstream changes arrive through reviewed dependency updates rather than silently changing test results.

On an update:

1. Validate all schemas and structural invariants.
2. Review added, removed, and reclassified cases.
3. Review schema and group-type changes before changing adapters.
4. Run the old and new corpus against the same implementation when diagnosing changed outcomes.
5. Record deliberate acceptable-case policy changes.

## Handle discovered vulnerabilities

Treat acceptance of an invalid cryptographic case as a potential security issue until triaged. Minimize the reproducer without publishing secret or exploit details. Report vulnerabilities privately to the affected implementation maintainers before proposing new public Wycheproof vectors, following the upstream contribution policy.
