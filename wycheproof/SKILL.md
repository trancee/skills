---
name: wycheproof
description: "Integrates and audits Project Wycheproof test vectors for cryptographic implementations. Use when selecting current vector files, validating them against repository schemas, mapping algorithm inputs to an API, enforcing valid/invalid/acceptable outcomes, or adding regression coverage. Don't use for NIST CAVP certification, generating new vectors, benchmarking, or general cryptographic design."
metadata:
  category: "cryptography"
  source: "https://github.com/C2SP/wycheproof"
  sourceVersion: "C2SP/wycheproof@dac1dd4729fd1f8dd9e1e9f3dce51d783da6c166"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-28T19:26:56+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T11:16:59+02:00"
---

# Project Wycheproof integration

## Procedures

**Step 1: Define the implementation boundary**

1. Identify the cryptographic primitive, public operation, parameter sets, encodings, and implementation version under test.
2. Test the same public API boundary used by callers, including key/signature/ciphertext parsers when malformed encodings are in scope.
3. Distinguish encryption from decryption, signing from verification, key generation from key validation, and encapsulation from decapsulation.
4. Exclude benchmarks, new-vector generation, and formal NIST validation from this workflow.

**Step 2: Pin the current corpus**

1. Use `https://github.com/C2SP/wycheproof` as the canonical source.
2. Pin a full upstream commit through a Git submodule, vendored files, or a versioned ecosystem package. Avoid an unpinned default-branch download in CI.
3. Select current vectors from `testvectors_v1/`. Use the historical `wycheproof-v0-vectors` tag only for an explicit legacy requirement.
4. Record the upstream commit, selected vector files, declared schemas, and update mechanism.
5. Read `references/integration.md` before choosing files or maintaining a vendored subset.

**Step 3: Validate vector data before testing crypto**

1. Read `references/vector-format.md`.
2. Read each vector's `schema` field and load that exact file from `schemas/` at the same pinned commit, including transitive schema references.
3. Treat current schemas as authoritative. Treat legacy files under upstream `doc/` as explanatory material that may be stale.
4. In a complete Wycheproof clone, run the repository's maintained formatter and `vectorgen lint` commands documented at the pinned revision.
5. For copied or packaged vectors, run JSON Schema validation with the project's validator.
6. Run the bundled structural checker:

   ```bash
   python3 scripts/check-vectors.py \
     --schemas-dir path/to/wycheproof/schemas \
     path/to/wycheproof/testvectors_v1
   ```

7. Stop if JSON contains duplicate keys, a schema is missing, test counts disagree, `tcId` values are duplicated/non-contiguous, results are unknown, or flags lack `notes` definitions.

**Step 4: Build schema-specific adapters**

1. Dispatch by declared schema and group `type`; reject unknown values rather than inferring a nearby format.
2. Keep generic JSON parsing separate from one adapter per cryptographic operation and encoding.
3. Apply group-level parameters to every case in that group.
4. Preserve input bytes exactly, including empty values, leading zeroes, malformed ASN.1, signed big-integer encodings, and unusual lengths.
5. Pass encoded keys, signatures, and ciphertexts directly to the public parser being tested. Avoid normalizing away the attack condition.
6. Distinguish documented rejection from crashes, timeouts, resource failures, unsupported parameters, and adapter bugs.

**Step 5: Enforce result semantics**

1. For `valid`, require acceptance and exact expected output or behavior.
2. For `invalid`, require documented rejection. Ensure authenticated decryption, verification, key validation, and key exchange do not release unauthorized output.
3. For `acceptable`, resolve every flag through root `notes` and apply a named project compatibility/security policy.
4. Report accepted and rejected acceptable cases separately. Never silently skip them or treat them automatically as valid.
5. If an acceptable case is accepted, require the specified output and all protocol safety conditions.
6. Include the vector filename, pinned commit, schema, group type/source, `tcId`, result, flags, expected behavior, and observed behavior in failures.

**Step 6: Cover every claimed capability**

1. Run every applicable group for each public parameter set, encoding, direction, and operation the implementation claims to support.
2. List unsupported groups explicitly with the corresponding API limitation. Do not silently filter unsupported cases.
3. Exercise both positive and negative behavior. A suite containing only known-answer `valid` vectors is incomplete.
4. Exercise every exposed direction: for example, test AEAD encryption output and decryption rejection when both APIs exist.
5. Keep a fast subset only when the complete selected corpus also runs in a defined CI job.
6. Pin corpus updates so added, removed, reclassified, or schema-changed cases arrive through review.

**Step 7: Diagnose failures safely**

1. Resolve case flags through `notes`; use them to understand intent, not as proof of root cause.
2. Reproduce one failing `tcId` through the same public adapter and minimize only outside the authoritative vector file.
3. Compare outcomes against an independent maintained implementation when the specification permits different behavior.
4. Treat acceptance of an invalid case as a potential security issue until triaged.
5. Report newly discovered vulnerabilities privately to affected maintainers before publishing exploit details or proposing public vectors.

**Step 8: Report and verify the integration**

1. Copy `assets/integration-report.md` when documenting an integration or audit.
2. Record source commit, files, schemas, implementation/API version, supported and unsupported groups, result policy, and counts.
3. Run the complete implementation test command and preserve its exact result.
4. Re-run schema and structural validation after every corpus or adapter change.
5. Confirm that every selected case produced an assertion or an explicit unsupported-policy outcome.
6. Report Wycheproof results as regression/security-test evidence, not as formal certification or proof that the cryptographic design is secure.

## Error Handling

- If a vector filename from old documentation is absent, inspect `testvectors_v1/` at the pinned commit and select by schema/algorithm rather than inventing a replacement name.
- If the declared schema is unknown, update the loader deliberately or pin the previous corpus. Do not parse it with another schema.
- If upstream `vectorgen` fails with excluded `encoding/json/jsontext` files, apply the pinned `doc/vectorgen.md` requirement for Go and `GOEXPERIMENT=jsonv2`.
- If `scripts/check-vectors.py` passes but schema validation fails, fix the schema-specific mismatch; the bundled checker validates only common structural invariants.
- If an invalid case returns output before an error, treat the output release as a failure even when the API eventually reports rejection.
- If an acceptable case has no documented project policy, report it as unresolved instead of silently passing or failing it.
- If an unsupported group is encountered, record it and verify that the implementation does not claim the corresponding capability.
- If a failure may expose a new vulnerability, restrict details and follow coordinated disclosure before upstream contribution.
