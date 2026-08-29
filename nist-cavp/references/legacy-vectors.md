# Static CAVP archive workflow

Read this reference when using NIST's downloadable ZIP archives and legacy CAVS response files for offline tests.

## Provenance and safe download

Copy the HTTPS download URL from the current algorithm landing page. Download to a temporary file, test the archive, calculate a local digest, then rename it atomically:

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

Record the landing page, direct URL, UTC retrieval time, SHA-256 digest, archive filename, algorithm/revision/operation, selected members, README, and governing validation-system document. A locally calculated digest supports reproducibility; it is not independent authenticity proof beyond HTTPS.

Keep the original archive unchanged. Before extraction, reject absolute member paths, `..` or backslash traversal, and unexpected symlinks. Apply the same checks to nested archives such as DRBG bundles.

## File roles

Read every bundled README and the governing validation-system document. Determine roles from content, not extension alone:

- `.rsp` commonly contains formatted inputs and expected responses;
- `.txt` commonly contains diagnostic intermediate values;
- some component archives publish the test corpus in `.txt`.

Intermediate values locate the first divergent internal step. They are not extra pass criteria unless the governing document says so.

## Lossless parsing

Treat CAVS files as ordered records, not generic INI data:

- `#` introduces comments;
- bracketed lines establish direction, algorithm, or parameter context;
- blank lines usually separate cases;
- `name = value` permits an empty value;
- field capitalization varies by family;
- fields may repeat in one case, such as DRBG `AdditionalInput`;
- bare markers such as `FAIL` carry semantics;
- `COUNT` is often local to a section.

Preserve ordered headers, ordered field pairs, repeated fields, markers, source entry, and line numbers. Convert to typed algorithm cases only after lossless parsing.

Run `scripts/check-rsp.py` to detect malformed lines and inventory sections, cases, repeated fields, and markers. Add `--require-field` and `--hex-field` only for fields whose semantics are known from the selected validation-system document.

## Encoding and length rules

Confirm every field in the family specification. Lengths are commonly bits.

- Interpret `Len = 0` as an empty message even when `Msg = 00` is a placeholder.
- Preserve empty plaintext, ciphertext, AAD, personalization, nonce, and additional-input values.
- Require byte-oriented lengths to be divisible by eight.
- Preserve significant-bit counts for bit-oriented vectors; avoid hashing or encrypting padding bits.
- Preserve leading zeroes and fixed-width big-endian integers.
- Use bit-capable APIs for CFB1 and other non-byte operations.
- Compare MACs and tags at the requested truncated length.

Reject malformed hex, missing required fields, unknown modes/test types, impossible lengths, and duplicate singleton fields. Do not silently repair inputs.

## Test-type execution

- **KAT/AFT/MMT:** execute the exact operation with group context and compare the specified output.
- **LDT:** generate the prescribed long input and stream it when possible instead of allocating a giant buffer.
- **MCT:** implement the exact recurrence from the validation-system document. Carry keys, IV/state, messages, and outputs across iterations; do not treat outer results as independent cases.
- **Authenticated decrypt:** require `FAIL` cases to reject authentication and release no plaintext.
- **Signature verification:** require `Result = P` to accept and `Result = F (...)` to reject.
- **DRBG:** follow the selected prediction-resistance/reseed scenario and exact instantiate, optional reseed, generate, generate, uninstantiate order; compare the specified generated output.
- **Randomized generation:** reproduce output only when the vector supplies deterministic entropy, private state, nonce/PMSN, or another controlled test seam.

Static CAVP archive success is regression evidence only. It does not create an algorithm certificate or replace ACVTS Production validation.
