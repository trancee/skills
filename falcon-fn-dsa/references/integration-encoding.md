# Integration and encoding

## Library acceptance

Require all of these before integration:

- Pinned artifact/source revision and upstream provenance.
- Exact Falcon v1.2 or published FN-DSA identity.
- Falcon-512 and/or Falcon-1024 explicitly selected.
- Exact key/signature format documented by the API.
- Randomized signing from a failure-reporting CSPRNG.
- Canonical decoding and strict length/trailing-byte rejection.
- Official vectors and cross-implementation evidence.
- Supported compiler/architecture matrix and side-channel statement.
- Security-reporting and update path acceptable to the deployment.

The corrected Falcon project API dated 2021-11-01 fixed faulty behavior in `shake256_init_prng_from_seed()` and `shake256_init_prng_from_system()`. Reject older or untraceable copies unless the fix and all local changes are reviewed directly. The NIST API, NIST vectors, PQClean, and pqm4 were reported unaffected by that particular issue.

liboqs currently lists Falcon as selected for upcoming NIST standardization, sourced from PQClean, with upstream maintenance `TBD` and OQS Tier 3 Community support. Use it for experiments or integrations only after independently accepting that support posture; library presence is not validation.

## API contract

Expose typed or tagged operations such as:

```text
keygen(parameters, rng) -> (public_key, private_key) | error
sign(parameters, format, private_key, message, rng) -> signature | error
verify(parameters, format, public_key, message, signature) -> valid | invalid | malformed
```

Keep `parameters` and `format` explicit and protocol-bound. Distinguish malformed encoding from cryptographically invalid signature internally. Avoid automatic algorithm negotiation driven by attacker-controlled bytes.

For the Falcon reference API:

- Use `logn = 9` for Falcon-512 and `logn = 10` for Falcon-1024.
- Allocate encoded keys and temporary buffers with the implementation's size macros.
- Set the input capacity before signing and consume the returned actual signature length.
- Pass `FALCON_SIG_COMPRESSED`, `FALCON_SIG_PADDED`, or `FALCON_SIG_CT` explicitly.
- Pass the same explicit format to `falcon_verify`/`falcon_verify_finish`; `sig_type = 0` infers the header and allows equivalent values to be transcoded among formats.
- Check every negative return code, including future unknown errors.

## Randomness

Use independent, failure-reporting randomness for key generation and every signature. The submission API consumes a SHAKE256 output-mode context seeded from either the OS or explicit test seed.

Production rules:

1. Seed through an OS CSPRNG or approved DRBG integration.
2. Propagate `FALCON_ERR_RANDOM` or equivalent.
3. Keep explicit seeds confined to deterministic test/vector harnesses.
4. Never derive signing randomness only from the key/message.
5. Never reuse a captured RNG context, salt, or streamed signing start state.
6. Exercise fork, snapshot/restore, VM clone, entropy-starvation, and concurrent-signing behavior when applicable.

A Falcon v1.2 signature hashes a uniformly random 40-byte salt with the message before hash-to-point. Repeated salts for the same message/key or deterministic custom variants invalidate a key security assumption.

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

## Streaming

For the reference API:

1. Call `falcon_sign_start` once; retain its 40-byte nonce and input-mode hash context.
2. Inject the complete message in order.
3. Call exactly one matching dynamic/tree finish operation using the same nonce/context.
4. For verification, call `falcon_verify_start`, inject the complete message, then call one `falcon_verify_finish` with the explicit expected format.
5. Invalidate contexts after finish/error/cancellation; never resume or fork them unless the exact API documents copying.
6. Test all chunk boundaries, including zero-length chunks and empty messages, against one-shot behavior.

## Secret objects

Encoded private keys, expanded private keys, FFT bases, LDL trees, signing RNG state, and temporary signing buffers are secret. Expanded keys are implementation-specific and the reference API requires preserved address alignment modulo 8 when moved. Keep expanded forms process-local, version-bound, nonportable, and excluded from backups/logs unless a reviewed storage contract explicitly covers them.
