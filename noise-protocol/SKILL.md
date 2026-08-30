---
name: noise-protocol
description: "Designs, integrates, tests, and reviews Noise Protocol Framework handshakes and transports. Use when selecting Noise patterns or cipher suites, mapping authentication and identity-hiding properties, configuring static/ephemeral/PSK inputs, binding prologue negotiation, integrating maintained Noise libraries, handling fallback/rekey/out-of-order records, validating protocol names and vectors, or auditing nonce, key, and state lifecycles. Don't use for TLS or QUIC, post-handshake Double Ratchet design, raw X25519/AEAD primitive implementation, generic VPN architecture, or inventing unreviewed handshake patterns."
compatibility: "Targets Noise Protocol Framework revision 34. The specification is official; revision-34 deferred patterns are unstable. Library support, extensions, fallback, algorithms, and test-vector formats vary by implementation. Helper requires Python 3.11+."
metadata:
  category: "cryptography"
  source: "https://noiseprotocol.org/noise.html"
  sourceVersion: "Noise Protocol Framework revision 34 (2018-07-11)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T17:56:22+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T17:56:22+02:00"
---

# Noise Protocol

## Step 1: Define the channel contract

1. DEFINE new integration | pattern/suite selection | interoperability | authentication | PSK | zero-RTT | fallback | framing | rekey | datagram transport | migration | security review.
2. IDENTIFY initiator/responder, one-way/interactive flow, authenticated identities, prior static-key knowledge, identity-hiding requirement, replay tolerance, early payloads, transport ordering, session termination, key rotation/storage, and adversary capabilities.
3. READ [Noise revision 34](https://noiseprotocol.org/noise.html), especially Sections 7, 13, and 14. Treat deferred patterns as unstable and extensions as separate specifications.
4. STATE peer-authentication policy outside Noise: certificate, pinned key, allowlist, or key continuity. Static-key possession alone does not decide whether a key belongs to an acceptable peer.
5. ROUTE raw X25519/AEAD/hash implementation to a primitive specialist, Ristretto work to `ristretto255`, primitive vectors to `wycheproof`/`nist-cavp`, and post-handshake ratcheting to its protocol-specific guidance.

Completion: roles, authentication, secrecy/identity/replay properties, early-data policy, trust store, framing, and session lifetime are explicit.

## Step 2: Inspect the integration and choose a library

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM protocol names, patterns/modifiers, algorithms, library/version/features, prologue/PSK/static/remote-static inputs, handshake and transport calls, handshake-hash use, rekey/nonce handling, framing limits, hard-coded secrets, and custom crypto/state-machine candidates.

READ `references/implementation-testing.md`. SELECT a maintained library that supports the exact revision, pattern, modifiers, suite, platform, constant-time primitive provider, invalid-key behavior, and vector/interoperability tests. Record audit status; repository popularity is not an audit.

Completion: one implementation/version and its unsupported features/security posture are documented; custom cryptography is absent or explicitly escalated for expert review.

## Step 3: Select the pattern and protocol name

READ `references/protocol-selection.md`.

1. CHOOSE a named vetted pattern from required prior-key knowledge and authentication/identity-hiding properties. Use `XX` as the general mutual-authentication starting point only when its properties satisfy the contract.
2. REQUIRE expert review before custom/deferred/extension patterns; never derive a new token sequence ad hoc.
3. CHOOSE one implemented suite, normally `25519` plus `ChaChaPoly` or hardware-backed constant-time `AESGCM`, and `SHA256`/`BLAKE2s`; justify deviations.
4. BUILD the exact protocol name `Noise_<pattern+modifiers>_<DH>_<cipher>_<hash>` and bind it unchanged on both peers.
5. USE each static key and PSK with one hash algorithm and only Noise-domain uses; rotate/migrate identity keys deliberately.

Completion: exact ASCII protocol name, pattern security properties, primitive provider, and key-domain constraints are fixed.

## Step 4: Initialize the handshake

READ `references/state-machine.md`.

1. ASSIGN initiator/responder roles and alternate `WriteMessage`/`ReadMessage` according to the pattern.
2. SUPPLY exactly the local/remote static or ephemeral inputs required by pre-messages; generate every sent ephemeral freshly with a CSPRNG.
3. CANONICALIZE negotiation context and mix identical bytes as prologue. Use a PSK—not prologue—when secret input must strengthen keys.
4. BOUND each complete handshake message to 65,535 bytes after public-key/tag overhead; derive the payload limit from the selected pattern and frame messages outside Noise.
5. ABORT and destroy the handshake state on DH, parse, or AEAD failure; never resume a partially failed state.

Completion: both peers start the same protocol/prologue with role-correct keys and a fresh handshake state.

## Step 5: Execute and authenticate the handshake

1. PROCESS each message once in pattern order; keep received static keys untrusted until application policy accepts them.
2. TREAT each handshake payload according to its pattern/message source and destination security grade. Early encryption is not final transport security.
3. ON final message, assign `Split()` state 1 to initiator->responder and state 2 to responder->initiator; never swap or share directions.
4. RETAIN `h` only when channel binding is required; bind higher-layer authentication to `h`, not `ck` or a transport key.
5. DELETE handshake state, ephemeral private keys, chaining keys, and temporary secrets after split/acceptance.

Completion: both peers agree on remote-key identity, handshake hash, payloads, and directional transport states.

## Step 6: Frame and run transport

READ `references/transport-framing.md`.

1. PREFIX/encapsulate Noise messages with authenticated application semantics for lengths, message types, version, and explicit end-of-stream/session termination.
2. LIMIT every Noise message to 65,535 bytes; account for the 16-byte AEAD expansion when sizing plaintext.
3. USE one monotonic nonce sequence per directional `CipherState`. Close before reserved maximum/overflow; rekey does not reset the nonce.
4. DEFINE AEAD-failure policy. In ordered streams, terminate the session; in datagrams, discard only under an explicit replay/window design.
5. SYNCHRONIZE rekey triggers per direction. For out-of-order delivery, transmit nonce metadata, call the library's supported nonce API, and reject every successfully used nonce replay.

Completion: framing resists truncation/confusion, directions never reuse key+nonce, and termination/rekey/replay behavior is testable.

## Step 7: Add PSK, zero-RTT, or fallback only when required

READ `references/psk-fallback.md`.

1. REQUIRE PSKs to be independent 32-byte secrets with 256 bits of entropy; keep them out of source/config/logs.
2. PLACE each `pskN` modifier exactly at the agreed message and provide PSKs in identical order.
3. TREAT zero-RTT payloads as replayable and weaker than completed transport; allow only idempotent/replay-safe application actions.
4. BIND negotiation/fallback choices into prologue or an authenticated compound-protocol transcript to prevent rollback.
5. IMPLEMENT fallback only if the library supports the exact modifier/state transfer; reverse roles and carry the prescribed semi-ephemeral state exactly.

Completion: PSK lifecycle, early-data replay policy, negotiation binding, and fallback transitions have cross-peer tests.

## Step 8: Verify protocol behavior

1. RUN the library's pinned revision-34 vectors for every supported pattern/suite/modifier; validate vector schema/hex lengths before execution.
2. RUN deterministic local vectors only with injected test keys/ephemerals; production key generation remains CSPRNG-owned.
3. CROSS-TEST at least one independent implementation for the exact protocol name and payload sequence.
4. TEST tampered/truncated/oversized/out-of-order/replayed messages, wrong prologue/static key/PSK/role/direction, invalid DH inputs, nonce exhaustion, rekey boundaries, and state reuse.
5. VERIFY handshake hash equality, payload bytes, transport round trips, rejection point, state destruction, and absence of secret logs.
6. COPY `assets/noise-review.md`; fill the channel contract, suite, pattern properties, key lifecycle, framing, failure policy, vectors, interoperability, and limitations.

Completion: positive vectors/interoperability and every relevant negative state transition pass without nonce/key reuse.

## Error Handling

- Unknown protocol name/extension -> stop and locate its governing specification plus implementation support; revision 34 alone is insufficient.
- Pattern authentication mismatch -> select a pattern from required prior-key knowledge; adding a certificate payload does not repair the wrong DH authentication shape.
- Remote static key accepted implicitly -> add explicit certificate/pinning/allowlist/key-continuity policy before application data.
- Prologue mismatch -> compare canonical negotiation bytes; never skip prologue to make peers connect.
- PSK is password/short token -> derive/provision a 32-byte high-entropy key through a reviewed mechanism; do not pass the password directly.
- Handshake/AEAD/DH failure -> destroy the handshake state and secrets; start a fresh handshake.
- Transport nonce exhausted/wrapped -> terminate and establish a new handshake; rekey cannot reset nonce.
- Datagram replay -> track accepted nonces in a bounded window before supporting out-of-order transport.
- Vector mismatch -> compare exact protocol name, role, prologue, keys, PSK order, message payload bytes, and failure index before changing crypto code.
- Custom pattern or primitive required -> stop implementation and require protocol/cryptography expert review plus independent interoperability evidence.
