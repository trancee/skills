---
name: nist-cavp-test-vectors
description: "Finds, downloads, parses, and integrates NIST CAVP or ACVP test vectors for cryptographic algorithms and primitive components. Use when adding NIST vectors, building an ACVP client, or verifying implementations against CAVP data. Don't use for Project Wycheproof attack vectors, formal validation without an accredited laboratory, or non-cryptographic test fixtures."
metadata:
  source: "https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/"
  createdAt: "2026-08-28T19:38:42+02:00"
  updatedAt: "2026-08-29T17:06:38+02:00"
---

# NIST CAVP and ACVP test vectors

Use this procedure to locate the authoritative vector family, preserve its provenance, parse it without changing semantics, and exercise a cryptographic implementation.

## 1. Choose CAVP examples or ACVP

Make this distinction before downloading anything:

- **Static CAVP archives** are NIST-published example vectors, usually ZIP files containing legacy CAVS `.rsp` response files and optional `.txt` intermediate values. Use them for local correctness and regression testing.
- **ACVP/ACVTS vector sets** are JSON requests generated for declared implementation capabilities. Use ACVTS Demo for client development and informal runs. Formal algorithm validation requires ACVTS Production through an accredited CST or 17ACVT laboratory.

Static vector success is not a CAVP validation and does not create a certificate. NIST explicitly states this on each vector page.

Choose ACVP when the algorithm/revision is absent from the static pages, when testing a current algorithm such as ML-KEM/ML-DSA/SLH-DSA, or when preparing validation evidence. Choose static CAVP archives for deterministic offline tests of a family that NIST still publishes there.

## 2. Identify the exact primitive

Write down the complete test identity:

- algorithm and standard revision;
- mode or operation (`encrypt`, `decrypt`, `keyGen`, `sigGen`, `sigVer`, `encapDecap`, component/primitive operation);
- parameter set, key size, curve, hash/XOF, tag size, and supported lengths;
- byte-oriented versus bit-oriented input;
- required test types: KAT/AFT, MCT, MMT, LDT, verification/negative cases, or algorithm-specific types.

Names that share a primitive are not interchangeable. Examples: AES-GCM versus GMAC, ECDSA signature verification versus signature-generation component, KAS-ECC versus CDH component, SHA-512 versus SHA-512/256, and ML-KEM `keyGen` versus `encapDecap`.

For formal ACVP work, also read the current [prerequisite table](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/prerequisites). Higher-level algorithms require separate testing of listed primitive dependencies.

The identity is complete only when it selects one NIST algorithm specification and one set of implementation capabilities.

## 3. Find the authoritative vectors

Start at the current [CAVP overview](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/) rather than guessing a media URL. Follow the algorithm family and use that page's **Test Vectors** links:

| Primitive family | NIST source page |
| --- | --- |
| AES/TDES and ECB, CBC, CFB, OFB, CTR | [Block Ciphers](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/block-ciphers) |
| CCM, CMAC, GCM/GMAC/XPN, KW/KWP/TKW, XTS | [Block Cipher Modes](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/cavp-testing-block-cipher-modes) |
| SHA-1, SHA-2, SHA-3, SHAKE | [Secure Hashing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/secure-hashing) |
| HMAC | [Message Authentication](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/message-authentication) |
| DSA, ECDSA, RSA signatures and key tests | [Digital Signatures](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/digital-signatures) |
| SP 800-108 KBKDF | [Key Derivation](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/key-derivation) |
| SP 800-90A DRBG | [Random Number Generators](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/random-number-generators) |
| KAS FFC/ECC and key confirmation | [Key Establishment](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/key-management/key-establishment) |
| ECC CDH, ECDSA sigGen component, SP 800-135 KDFs, RSADP, RSASP1 | [Component Testing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/component-testing) |
| Historical algorithms only | [Retired Testing](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/retired-testing) |

For a primitive component, inspect **Component Testing** before using a full-algorithm archive. For newer algorithms or revisions, use the current [ACVP Supported Algorithms](https://pages.nist.gov/ACVP/#supported) list and open the linked algorithm specification. The index is the source of truth for the exact ACVP algorithm name, mode, revision, test-group properties, request fields, and response fields.

Do not infer current approval from the existence of an old ZIP. Check the current standard, CAVP page, ACVP support status, and prerequisite page.

## 4. Download immutably

Use the HTTPS URL copied from the current NIST page. Download to a temporary file, verify that transfer and archive parsing succeed, compute a local digest, then atomically rename it:

```bash
url='https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Algorithm-Validation-Program/documents/.../vectors.zip'
dest='tests/vectors/nist/vectors.zip'
mkdir -p "$(dirname "$dest")"
tmp="${dest}.part"
curl --fail --location --proto '=https' --tlsv1.2 --output "$tmp" "$url"
unzip -t "$tmp"
sha256sum "$tmp"
mv "$tmp" "$dest"
```

NIST's vector pages generally do not publish a separate checksum. A locally recorded SHA-256 digest makes future downloads and repository changes reproducible; it is not independent authenticity proof beyond the HTTPS transfer.

Alongside the archive, record:

- vector landing-page URL and direct download URL;
- UTC retrieval date;
- SHA-256 digest;
- archive filename;
- algorithm, standard/revision, operation, and selected internal files;
- any NIST README or validation-system document governing interpretation.

Keep the original archive unchanged. Prefer reading entries directly. Before extraction, list names and reject absolute paths, `..` traversal, backslash traversal, and unexpected symlink entries. Extract into a new dedicated directory only after the list passes. Nested archives, notably DRBG bundles, require the same integrity and path checks at every layer.

Refresh the landing page when updating vectors; direct media URLs can remain reachable after their algorithm or revision has become obsolete.

## 5. Read the archive before writing a parser

Read every bundled `README` and the linked validation-system document. Determine each file's role from those sources and its content, not from the extension alone. Most `.rsp` files contain test inputs and expected responses, while `.txt` often contains debugging intermediates; some component archives, including ECC CDH, publish the actual test corpus only as `.txt`.

Legacy CAVS `.rsp` is a line-oriented format, not a generic INI file:

- `#` lines are comments and often identify generator version and date.
- `[ENCRYPT]`, `[DECRYPT]`, `[P-256,SHA-256]`, `[L = 32]`, and similar headers establish context for following cases.
- blank lines usually separate cases;
- `name = value` fields may have an empty value;
- field names and capitalization vary by family;
- a field can occur more than once in one case, such as two DRBG `AdditionalInput` calls;
- bare markers such as `FAIL` carry semantics;
- `COUNT` is normally local to a group, not a globally unique ID.

Represent parsed data as ordered groups and ordered field pairs, plus markers and source line numbers. A global map loses repeated fields and group context. Convert to algorithm-specific typed cases only after parsing the lossless structure.

Reject malformed hex, missing required fields, unknown test types/revisions, impossible lengths, and duplicate singleton fields. Preserve leading zeroes and the declared bit length. Compare decoded bytes or integers according to the algorithm specification, not normalized display strings.

## 6. Preserve length and encoding semantics

CAVP and ACVP length fields are commonly measured in **bits**. Confirm each field in the family specification.

Apply these rules:

- `Len = 0` means an empty message even when a legacy file writes `Msg = 00` as a placeholder.
- Empty `PT`, `CT`, `AAD`, personalization strings, and additional inputs are valid.
- Byte-oriented files require lengths divisible by eight.
- Bit-oriented files require a bit-capable implementation path. Preserve the exact significant-bit count and follow that algorithm's stated bit ordering; do not round up and hash/encrypt padding bits.
- Preserve big-endian unsigned integer and fixed-width field semantics for ECC/RSA values; leading zeroes can be significant to the encoded width.
- CFB1 and other non-byte modes require bit-level APIs or a tested adapter.
- Truncated MAC/tag output must be compared at the requested `Tlen`/`tagLen`, not at the primitive's full output size.

Assert decoded lengths before invoking the implementation. Silent padding, truncation, odd-nibble repair, or integer re-encoding turns a vector test into a different test.

## 7. Execute by test type

### Direct-answer tests: KAT/AFT/MMT/LDT

Build inputs from group context plus case fields, call the exact primitive operation, and compare the specified output. MMT covers multi-block/message cases. LDT can use generated long data described by its algorithm specification; do not allocate a giant buffer when a streaming API can feed the prescribed pattern.

### Monte Carlo tests

Implement the recurrence from the linked validation-system or ACVP algorithm document. A `.rsp` MCT entry is not a set of independent one-shot cases. Carry the key, IV/state, message, and digest/output forward exactly as specified. ACVP responses commonly require a `resultsArray` containing each outer-loop result.

Use bundled `.txt` intermediate values to identify the first divergent iteration. They are diagnostic checkpoints, not additional pass criteria unless the README says otherwise.

### Authenticated decryption and verification

Negative cases are first-class tests:

- GCM/CCM decrypt `FAIL`: require authentication rejection and no released plaintext.
- Signature `Result = P`: verification must accept.
- Signature `Result = F (...)`: verification must reject; the parenthesized reason is diagnostic metadata.
- Public-key/key-pair validation vectors can include invalid components and must exercise validation rather than successful construction shortcuts.

A harness that skips `FAIL`/`F` cases is incomplete.

### Signature and key generation

Randomized generation cannot generally be checked by comparing one expected signature/key unless the vector supplies the private key, per-message secret, entropy stream, or deterministic mode and the implementation exposes a controlled test seam. For legacy ECDSA, the `.txt` generation files include `d` and `k` specifically for reproducing `r` and `s`.

When randomness cannot be injected safely, use verification vectors for deterministic regression coverage and use the algorithm-specific ACVP generation flow for validation. Never replace production randomness globally to satisfy a test vector.

### DRBG

Follow the exact scenario and ordering selected by the archive: prediction resistance on/off, reseed supported/unsupported, derivation function, primitive, and declared lengths. Legacy DRBG response cases typically perform instantiate, optional reseed, generate, generate, then compare `ReturnedBits` from the second generate. Repeated `AdditionalInput` fields correspond to separate generate calls. Intermediate `.txt` files expose `V`, `Key`, `C`, and/or `reseed_counter` after operations for diagnosis.

## 8. Integrate into tests

Dispatch on algorithm, revision, mode, group parameters, direction, and test type. Keep one adapter at the implementation boundary so the parser remains independent of the crypto library API.

For every supported capability:

1. run all applicable positive vectors;
2. run all applicable negative/verification vectors;
3. cover every implemented key size, curve/parameter set, tag/output size, and direction represented by the source;
4. run stateful MCT/DRBG sequences according to their documents;
5. identify unsupported vector groups explicitly instead of silently filtering them.

A useful failure names archive, entry, group context, `COUNT` or `tgId`, `tcId`, operation, declared lengths, expected value, and actual value. For stateful tests, also report the first divergent iteration/checkpoint.

Keep a small direct-answer subset in fast CI only if the complete applicable corpus also runs in a defined full-suite job. Do not hand-copy a few vectors and call the primitive covered.

## 9. Use ACVP/ACVTS vector sets

ACVP wire data is JSON and is not interchangeable with legacy `.rsp`.

1. Obtain ACVTS Demo access using NIST's [access procedure](https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/how-to-access-acvts). Demo uses credentials and a client certificate; it is semi-volatile. Production access is restricted to accredited laboratories.
2. Read the [base protocol](https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html) and the linked current algorithm specification.
3. Register only capabilities the implementation actually supports. The server generates matching test sessions and vector sets.
4. Download each vector set from its test-session URL. Preserve the protocol envelope and `vsId`.
5. Process each `testGroups` entry using its `tgId`, group parameters, `testType`, and ordered `tests`. Preserve every `tcId` in the response.
6. Emit only the response fields required by that algorithm/revision. MCT and stateful algorithms can require arrays or multi-step outputs.
7. POST results to `/testSessions/{testSessionId}/vectorSets/{vectorSetId}/results`, then retrieve the disposition. Diagnose failures by `vsId`/`tgId`/`tcId`.

A test session contains multiple vector sets. One request and one response correspond to each `vsId`; groups share properties under `tgId`; `tcId` identifies individual operations. Fail closed on an unsupported revision or `testType` rather than applying another revision's semantics.

For a sample session, ACVP permits retrieval of expected results from `/testSessions/{testSessionId}/vectorSets/{vectorSetId}/expected`. Expected results are only guaranteed when the session resource has `isSample: true`. Do not design a production validation client around access to expected answers.

The CAVP server generates vectors but does not run the implementation. The client/harness must execute every case and return correctly structured results.

## 10. Completion checks

Work is complete when:

- the source page still identifies the selected algorithm/revision;
- the original archive or ACVP request is preserved with provenance;
- archive integrity and safe member paths were checked;
- the README and algorithm-specific procedure were applied;
- bit lengths, empty values, repeated fields, leading zeroes, and group context survive parsing;
- positive, negative, and stateful cases applicable to every claimed capability run against the real implementation;
- failures identify the original vector case;
- static vectors are described as regression evidence, not NIST validation;
- formal-validation work uses ACVTS Production through an accredited lab and includes prerequisite algorithms.

## Primary references

- CAVP overview: https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/
- ACVP supported algorithms: https://pages.nist.gov/ACVP/#supported
- ACVP base protocol: https://pages.nist.gov/ACVP/draft-fussell-acvp-spec.html
- ACVTS access: https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/how-to-access-acvts
- Algorithm prerequisites: https://csrc.nist.gov/projects/cryptographic-algorithm-validation-program/prerequisites
