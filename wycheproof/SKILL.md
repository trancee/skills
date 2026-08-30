---
name: wycheproof
description: "Integrates/audits Project Wycheproof vectors. Use for current corpus selection, schema validation, crypto-API adapters, valid/invalid/acceptable policy, or regression coverage. Don't use for NIST certification, vector generation, benchmarks, or general crypto design."
metadata:
  category: "cryptography"
  source: "https://github.com/C2SP/wycheproof"
  sourceVersion: "C2SP/wycheproof@dac1dd4729fd1f8dd9e1e9f3dce51d783da6c166"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:48:01+02:00"
---

# Wycheproof

## 1. Boundary+source

1. DEFINE primitive, public operation, params, encodings, sizes, implementation version; test caller API including parsers.
2. Distinguish encrypt/decrypt, sign/verify, keygen/key-validation, encaps/decaps.
3. PIN full `C2SP/wycheproof` commit via submodule/vendor/versioned package; no default branch in CI.
4. Current=`testvectors_v1/`; v0 tag only explicit legacy.
5. RECORD commit, vectors, schemas, update mechanism.
6. READ `references/integration.md` before selection/vendor work.

## 2. Validate corpus

1. READ `references/vector-format.md`.
2. Each vector `schema` -> exact `schemas/` file + transitive refs at same commit. Unknown => reject.
3. Current schema authoritative; `doc/` may be stale.
4. Full clone: run pinned `vectorgen fmt --check` + `vectorgen lint`.
5. Vendor/package: JSON Schema validator +:
   ```bash
   python3 scripts/check-vectors.py \
     --schemas-dir path/to/wycheproof/schemas \
     path/to/wycheproof/testvectors_v1
   ```
6. STOP on duplicate JSON keys, missing schema, count mismatch, duplicate/noncontiguous `tcId`, unknown result, undefined flag.

## 3. Adapter

- dispatch by declared schema + group `type`; unknown => reject
- generic JSON parse separate from operation/encoding adapter
- group params apply to every case
- preserve raw bytes: empty, leading zeros, malformed ASN.1, signed bigint, unusual lengths
- parser in public boundary receives raw key/signature/ciphertext; no normalization
- distinguish rejection vs crash/timeout/resource/unsupported/adapter bug

## 4. Result policy

- `valid` => accept + exact expected output/behavior
- `invalid` => documented reject; no unauthorized plaintext/key/shared secret/verified result
- `acceptable` => resolve flags via root `notes`; apply named project policy; report accepted/rejected separately; if accepted require expected output+safety
- failure record: file, commit, schema, group type/source, `tcId`, result, flags, expected, observed

## 5. Coverage

1. RUN every applicable group for each claimed parameter, encoding, direction, operation.
2. Unsupported groups explicit + API limitation; no filtering.
3. Positive + negative required; each exposed direction tested.
4. Fast subset allowed only with defined full selected corpus CI job.
5. Corpus updates pinned+reviewed for add/remove/reclassification/schema change.

## 6. Diagnose+report

- resolve flags via `notes`; not root-cause proof
- reproduce one `tcId` through same public adapter; minimize outside source vector only
- compare independent implementation when spec permits variance
- accepted invalid => potential security issue; private coordinated disclosure before public details/vectors
- OUT: copy `assets/integration-report.md`; commit/files/schemas/API/version/groups/policy/counts/exact commands
- verify all selected cases asserted or explicitly unsupported
- result = regression/security evidence, never certification/design proof

## Fail

- old filename absent => select current by schema+algorithm
- unknown schema => update loader OR pin prior corpus; never substitute schema
- `vectorgen` excluded `encoding/json/jsontext` => pinned `doc/vectorgen.md` Go+`GOEXPERIMENT=jsonv2`
- structural pass + schema fail => fix schema mismatch
- output released before invalid error => FAIL
- acceptable without policy => unresolved
- unknown group => record unsupported; ensure capability not claimed
- possible vulnerability => restrict details; coordinate
