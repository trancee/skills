# Transport, framing, and lifecycle

Normative source: [Noise revision 34 Sections 3, 11, 13, and 14](https://noiseprotocol.org/noise.html).

Noise messages contain no internal type or length fields and are at most 65,535 bytes. Transport ciphertext adds 16 bytes, so maximum plaintext is 65,519 bytes. The application owns record boundaries, version/type metadata, padding, fragmentation, and explicit session/end-of-stream signals.

A 16-bit big-endian outer length is the revision-34 recommendation when a length field is needed. Authenticate semantic metadata either inside encrypted payloads or through a protocol-specific binding; unauthenticated negotiation can enable rollback.

Each transport direction owns one `CipherState`. Ordered transport consumes nonces monotonically. Authentication failure does not increment the failed decrypt nonce in the abstract state, but an ordered stream should normally terminate because state/framing may be desynchronized.

Nonce `2^64-1` is reserved for `REKEY`; normal encryption may not reach/wrap it. On exhaustion, terminate and establish a new handshake. `Rekey()` changes only `k`, not `n`; peers must trigger it at the same directional boundary.

For datagrams/out-of-order transport:
1. carry the encryption nonce outside the Noise ciphertext
2. reject nonces outside a bounded receive window
3. set the receive nonce only through the library's supported API
4. authenticate/decrypt
5. mark a nonce consumed only after successful authentication
6. reject every consumed nonce replay

This introduces denial-of-service, window, concurrency, and persistence concerns beyond Noise. Never share one `CipherState` concurrently without serialized nonce ownership.

Half-duplex mode reuses one state in both directions only under strict alternation. Any simultaneous sends can repeat key+nonce catastrophically; prefer ordinary two-state transport.
