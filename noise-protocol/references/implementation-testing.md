# Implementation and testing review

Sources: [Noise homepage implementations](https://noiseprotocol.org/), [revision 34](https://noiseprotocol.org/noise.html), and [test-vector format](https://github.com/noiseprotocol/noise_wiki/wiki/Test-vectors).

## Library selection

Record exact version/commit, maintenance, revision, patterns/modifiers, primitive providers, target/platform support, constant-time claims, invalid-DH behavior, audit history, vector corpus, and unsupported features. A library README claiming “hard to misuse” or a large user count is not a formal audit.

Prefer opaque handshake/transport state types, role-specific constructors, owned nonce progression, CSPRNG key generation, fixed-size key validation, explicit errors, zeroization, and APIs that prevent post-failure/post-split reuse. Avoid reconstructing Noise from generic DH/HKDF/AEAD calls.

## Vector execution

Noise vector JSON contains `protocol_name`, role prologues/keys/PSKs, optional fallback fields and handshake hash, plus alternating payload/ciphertext messages. Validate strict JSON/hex, key/PSK sizes, mandatory fields, message count, and expected-failure semantics before adapters.

Use pinned vector bytes from an implementation corpus and retain source URL/commit/digest. Vectors prove conformance to those cases, not implementation safety or protocol suitability.

Test matrix:
- every supported pattern/suite/modifier and both roles
- empty/max payloads and 65,535-byte ciphertext boundary
- deterministic injected statics/ephemerals/PSKs/prologues
- handshake hash and every ciphertext byte against vectors
- cross-implementation transcript for exact protocol name
- bit flips/truncation/trailing/oversized data at every message
- wrong role/order/prologue/static/PSK and invalid DH public keys
- post-failure, post-split, duplicate-read/write, wrong-direction state reuse
- rekey sync/desync and nonce exhaustion/wrap
- datagram loss/reorder/replay/window concurrency when supported

Production randomness/secret storage needs separate runtime tests; deterministic vector RNG must be unreachable from production constructors.
