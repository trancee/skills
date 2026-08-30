# Static CAVP workflow

USE for downloadable archives/legacy CAVS files.

## Acquire

Current landing page URL -> temp -> archive test -> digest -> atomic rename:
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
RECORD landing/direct URLs, UTC time, SHA-256, archive, algorithm/revision/operation, selected members, README, governing doc. Digest=reproducibility, not authenticity beyond HTTPS.
KEEP original unchanged. Before any extraction reject absolute path, `..`, backslash traversal, unexpected symlink; recurse for nested archives.

## Parse losslessly

Read every README+governing doc. File role from content, not suffix (`.rsp` usually cases; `.txt` may be intermediate OR corpus).
CAVS model:
- `#` comment
- `[header]` context
- blank usually case boundary
- `name = value`, including empty
- case varies; fields may repeat; bare marker has semantics; `COUNT` section-local

PRESERVE ordered headers/fields/repeats/markers/source line. Typed conversion after lossless parse.
RUN `scripts/check-rsp.py`; add `--require-field`, `--hex-field`, `--allow-marker` only from selected spec.

## Encoding

- lengths commonly bits; `Len=0` => empty even if `Msg=00` placeholder
- preserve empty values, leading zeros, fixed-width BE integers
- byte API requires length%8=0; bit vectors retain significant bits; never process padding
- CFB1 etc require bit API
- MAC/tag compare at requested truncation
- reject malformed hex/missing/unknown/impossible/duplicate singleton; no repair

## Execute

- KAT/AFT/MMT: exact operation+context
- LDT: prescribed generation; stream
- MCT: exact state recurrence across iterations
- auth decrypt `FAIL`: reject, no plaintext
- signature `P` accept; `F` reject
- DRBG: exact instantiate/[reseed]/generate/generate/uninstantiate scenario
- randomized generation: only supplied deterministic entropy/private-state/nonce seam

PASS=regression evidence only; never certificate/Production substitute.
