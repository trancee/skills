---
name: nist-cavp
description: "Finds, downloads, parses, and integrates NIST CAVP and ACVP cryptographic test vectors. Use when locating vectors for primitives or components, building offline regression tests from CAVP archives, implementing ACVP request/response handling, or preparing algorithm validation work. Don't use for Project Wycheproof attack vectors, claiming certification from static vectors, or non-cryptographic fixtures."
metadata:
  source: "https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/"
  createdAt: "2026-08-28T19:38:42+02:00"
  updatedAt: "2026-08-29T17:30:59+02:00"
---

# NIST CAVP and ACVP vectors

## Procedures

**Step 1: Choose the validation track**

1. Choose static CAVP archives for deterministic offline regression tests of algorithms and components with published legacy vectors.
2. Choose ACVP/ACVTS for capability-matched JSON vector sets, current algorithms or revisions absent from static pages, ACVP client work, or preparation for formal validation.
3. Use ACVTS Demo for client and implementation practice. Use ACVTS Production through an accredited CST or 17ACVT laboratory for certificate-issuing work.
4. State explicitly that static vectors and Demo results do not create a CAVP certificate.

**Step 2: Identify the exact primitive and operation**

1. Record the algorithm, standard revision, mode or component operation, parameter set, key size, curve, hash/XOF, tag/output size, supported lengths, and byte/bit orientation.
2. Distinguish nearby operations such as AES-GCM versus GMAC, ECDSA `sigVer` versus a `sigGen` component, KAS-ECC versus CDH component, SHA-512 versus SHA-512/256, and KEM `keyGen` versus `encapDecap`.
3. Record required test types such as KAT/AFT, MMT, MCT, LDT, generation, verification, negative, or stateful scenarios.
4. Define the implementation's actual capabilities before selecting vectors or registering with ACVTS.

**Step 3: Locate the authoritative source**

1. Read `references/algorithm-sources.md`.
2. Start from the current CAVP algorithm landing page and follow its Test Vectors links instead of guessing a media URL.
3. For a primitive component, inspect Component Testing before selecting a full-algorithm archive.
4. For ACVP, use the current supported-algorithms index and linked algorithm-specific specification to select the exact algorithm name, revision, mode, capability fields, test types, and response schema.
5. Check the current prerequisite table and include every separately required primitive validation.
6. Do not infer current approval or support from a historical ZIP that remains downloadable.

**Step 4: Acquire and preserve vectors**

1. For static archives, read `references/legacy-vectors.md`, download over HTTPS from the current landing page, verify archive integrity, inspect safe member paths, and calculate a local SHA-256 digest.
2. Preserve the original archive unchanged with landing page, direct URL, retrieval time, digest, algorithm/revision, selected members, README, and governing validation-system document.
3. Apply the same path and integrity checks to every nested archive.
4. For ACVP, read `references/acvp.md`, preserve the protocol envelope and identifiers, and protect client certificates, private keys, JWTs, and credentials.

**Step 5: Parse without changing semantics**

1. Read every bundled README and governing algorithm/validation-system document before writing an adapter.
2. Parse legacy CAVS files as ordered headers, ordered field pairs, repeated fields, bare markers, cases, and source line numbers.
3. Run the structural checker on applicable response files:

   ```bash
   python3 scripts/check-rsp.py path/to/vectors
   ```

4. Add `--require-field` and `--hex-field` only after the selected specification defines those fields. Add `--allow-marker` only for a documented bare marker.
5. Preserve empty values, leading zeroes, fixed widths, repeated DRBG inputs, bit lengths, and case-local identifiers.
6. Reject malformed hex, unknown test types/revisions, impossible lengths, missing fields, duplicate singleton fields, and unsupported bit-oriented inputs.

**Step 6: Execute static vectors by test type**

1. Build typed cases from lossless parsed data plus section/group context.
2. Execute KAT/AFT/MMT cases directly against the exact implementation operation.
3. Implement MCT recurrences from the governing document; carry key, IV/state, message, and output between iterations rather than treating results independently.
4. Stream LDT inputs according to the prescribed generation rule instead of avoidably allocating a giant message.
5. Require authenticated-decrypt `FAIL` cases to reject without releasing plaintext.
6. Require signature `Result = P` cases to accept and `Result = F (...)` cases to reject.
7. Execute DRBG operations in the exact prediction-resistance/reseed scenario and sequence.
8. Reproduce randomized generation only through a controlled entropy/nonce/private-state seam explicitly supplied by the vector procedure.

**Step 7: Execute ACVP vector sets**

1. Follow `references/acvp.md` and the current base protocol.
2. Register only implemented capabilities and required prerequisites.
3. Retrieve every vector set in the test session and preserve `vsId`, `tgId`, and `tcId` exactly.
4. Dispatch by algorithm, revision, mode, group parameters, and `testType`; fail closed on unknown values.
5. Emit only the response fields required by that algorithm specification, including ordered arrays or stateful outputs for MCT, DRBG, and KAS cases.
6. Submit one response per `vsId`, retrieve the disposition, and diagnose failures by the original identifier hierarchy.
7. Use expected-result endpoints only for sample sessions that advertise `isSample: true`; keep Production clients independent of expected-answer access.

**Step 8: Integrate complete capability coverage**

1. Run every applicable positive, negative, verification, direction, key size, parameter set, curve, tag/output size, and stateful group represented by each claimed capability.
2. Identify unsupported groups explicitly instead of silently filtering them.
3. Keep a fast subset only when the complete applicable corpus remains in a defined full-suite job.
4. Report failures with source/archive, entry or vector set, section/group context, `COUNT` or `vsId/tgId/tcId`, operation, lengths, expected value, actual value, and first divergent stateful checkpoint.
5. Keep parsers independent of the cryptographic API through a narrow operation adapter.

**Step 9: Report evidence accurately**

1. Copy `assets/integration-report.md` for an integration or validation report.
2. Record the exact test identity, vector source, provenance, coverage, prerequisites, commands, outcomes, unsupported capabilities, and limitations.
3. Describe static archive and Demo success as regression/test evidence only.
4. Claim formal algorithm validation only with qualifying ACVTS Production work through an accredited laboratory and the resulting listed certificate.

## Error Handling

- If the algorithm/revision cannot be selected unambiguously, stop vector selection and resolve the exact implementation capability first.
- If a direct media URL works but the landing page no longer lists the vector, treat it as historical until current status is established.
- If archive members contain unsafe paths or unexpected symlinks, reject extraction and inspect the archive without writing members.
- If `scripts/check-rsp.py` rejects a documented marker or field shape, read the governing validation-system document before extending parser rules.
- If a bit-oriented case reaches a byte-only API, mark the capability unsupported or implement a verified bit adapter; never round the length.
- If MCT or DRBG output first diverges internally, compare the bundled intermediate checkpoints before changing the primitive.
- If ACVP returns an unknown revision or test type, update against the linked algorithm specification rather than applying another revision's semantics.
- If Production access or prerequisite evidence is unavailable, complete offline or Demo work and report formal validation as blocked, not achieved.
