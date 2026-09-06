# Integration and encoding

## Library acceptance

Require all of these before integration:

- Pinned artifact/source revision and upstream provenance.
- Explicit legacy Falcon v1.2 or provisional c-fn-dsa identity.
- Standard degree 512 and/or 1024 explicitly selected.
- Exact key/signature format documented by the selected source revision.
- Randomized signing from a failure-reporting CSPRNG.
- Canonical decoding and strict length/trailing-byte rejection.
- Matching vectors and cross-implementation evidence for the declared contract.
- Supported compiler/architecture matrix and side-channel statement.
- Security-reporting and update path acceptable to the deployment.

Use `pornin/c-fn-dsa` at a pinned revision as the active implementation reference for provisional FN-DSA work. Its README explicitly says that no FN-DSA draft exists yet, current behavior is a best guess, compatibility may break, and version 1.0 will follow final FIPS 206. This repository is implementation evidence, not a normative or validated FN-DSA definition.

PQClean is retired, archived read-only, and no longer maintained. Do not select its Falcon code for new integrations. Existing PQClean-derived deployments need explicit local-maintenance and migration ownership; replacing the source does not by itself migrate wire formats or stored keys.

The corrected Falcon project API dated 2021-11-01 remains relevant only to legacy Falcon v1.2. It fixed faulty `shake256_init_prng_from_seed()` and `shake256_init_prng_from_system()` behavior; reject older or untraceable legacy copies unless the fix and all downstream modifications are proven.

## API contract

Expose typed or tagged operations such as:

```text
keygen(parameters, rng) -> (public_key, private_key) | error
sign(parameters, format, private_key, message, rng) -> signature | error
verify(parameters, format, public_key, message, signature) -> valid | invalid | malformed
```

Keep `parameters` and `format` explicit and protocol-bound. Distinguish malformed encoding from cryptographically invalid signature internally. Avoid automatic algorithm negotiation driven by attacker-controlled bytes.

For the active provisional c-fn-dsa API in `fndsa.h`:

- Pin the exact commit; pre-1.0 keys, signatures, vectors, encodings, and APIs have no compatibility promise.
- Use `FNDSA_LOGN_512` or `FNDSA_LOGN_1024`; weak-degree APIs are test/research-only.
- Allocate encoded keys/signatures with `FNDSA_SIGN_KEY_SIZE`, `FNDSA_VRFY_KEY_SIZE`, and `FNDSA_SIGNATURE_SIZE` from that revision.
- Bind context (0..255 bytes) and hash identifier explicitly: raw message, named prehash OID, or 64-byte external `mu` are distinct contracts.
- Use `fndsa_keygen`, `fndsa_sign`, and `fndsa_verify` for the ordinary OS-RNG path; check zero/error returns and output-buffer sizes.
- Treat `fndsa_keygen_seeded` and `fndsa_sign_seeded` as vector/test or reviewed bare-metal entropy interfaces. Store encoded signing keys, never key-generation seeds.
- Expect final FIPS 206 to require a fresh 40-byte signing seed per attempt; do not substitute deterministic signing.

For the historical Falcon v1.2 reference API:

- Use `logn = 9` for Falcon-512 and `logn = 10` for Falcon-1024.
- Allocate buffers with that API's macros and pass `FALCON_SIG_COMPRESSED`, `FALCON_SIG_PADDED`, or `FALCON_SIG_CT` explicitly.
- Pass the same explicit format to verification; `sig_type = 0` allows representation transcoding.
- Keep this path identified as Falcon v1.2, not FN-DSA.

## Randomness

Use independent, failure-reporting randomness for key generation and every signature. The ordinary c-fn-dsa APIs call the operating-system RNG; its seeded APIs make the caller responsible for sufficient entropy. The legacy Falcon API consumes a caller-seeded SHAKE256 output context.

Production rules:

1. Prefer `fndsa_keygen`/`fndsa_sign` on supported systems and propagate zero/error returns.
2. For reviewed bare-metal use, supply seeded APIs with fresh CSPRNG/DRBG output of the required entropy; never a reproducible application seed.
3. Keep explicit deterministic seeds confined to vector tests.
4. Never derive signing randomness only from the key/message.
5. Never reuse a captured RNG state, salt, signing seed, or message representative.
6. Exercise fork, snapshot/restore, VM clone, entropy-starvation, and concurrent-signing behavior when applicable.

Falcon v1.2 uses a random 40-byte salt. Provisional c-fn-dsa generates a fresh 40-byte signing seed per attempt. Reuse or unexpected deterministic behavior is a potential key-security incident.

## Canonical parsing

At the public boundary:

1. Check algorithm/version metadata before parsing bytes.
2. Check exact key length and encoded degree/header.
3. Decode coefficients with the exact signed/unsigned ranges and bit order.
4. Reject noncanonical zero, forbidden coefficients, nonzero unused terminal bits, malformed unary coding, partial padding, nonzero padding, and trailing bytes.
5. Check signature norm and every verification equation; parsing success is not verification.
6. Return one protocol-level invalid result where distinguishing malformed from bad signature would expose an oracle.

Preserve original bytes when a protocol signs, hashes, logs, or identifies an encoding. Do not decode and re-encode attacker input before the verification decision.

## Signature formats

- **Compressed:** variable size and shortest on average. Carry an explicit bounded length in the enclosing protocol.
- **Padded:** canonical compressed value plus zero padding to an exact parameter-dependent size. Reject partial or nonzero padding.
- **CT:** fixed-size representation intended to avoid timing leakage about signature value/message hash in the reference implementation; it is not a blanket constant-time guarantee for the caller, platform, or build.

Choose one wire format per protocol version. If multiple formats are accepted for migration, give each a distinct algorithm/format identifier and define downgrade behavior.

## Message processing and streaming

For c-fn-dsa, bind the hashed verifying key, context, and hash identifier into the 64-byte `mu` exactly as its pinned API defines. `FNDSA_HASH_ID_RAW`, named prehash identifiers, and `FNDSA_HASH_ID_EXTMU` are not interchangeable. Use `fndsa_compute_mu_start` only to stream raw-message hashing into the caller's SHAKE256 state, then sign/verify the exact resulting `mu` contract.

For the legacy Falcon streamed API:

1. Call `falcon_sign_start` once; retain its 40-byte nonce and input-mode hash context.
2. Inject the complete message in order.
3. Call exactly one matching dynamic/tree finish operation using the same nonce/context.
4. For verification, call `falcon_verify_start`, inject the complete message, then call one `falcon_verify_finish` with the explicit expected format.
5. Invalidate contexts after finish/error/cancellation; never resume or fork them unless the exact API documents copying.
6. Test all chunk boundaries, including zero-length chunks and empty messages, against one-shot behavior.

## Secret objects

Encoded signing keys, hashed verifying-key values embedded in signing keys, signing seeds/RNG state, legacy expanded keys, FFT bases, LDL trees, and temporary signing buffers are secret. Keep implementation-specific expanded forms process-local, version-bound, nonportable, and excluded from backups/logs unless a reviewed storage contract explicitly covers them.
