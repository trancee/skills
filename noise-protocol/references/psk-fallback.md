# PSKs, early data, and fallback

Normative source: [Noise revision 34 Sections 6, 9, 10, and 14](https://noiseprotocol.org/noise.html).

A prologue confirms identical public context in the handshake hash; it does not add secret key material. A PSK is exactly 32 bytes with 256 bits of entropy and is mixed into keys and transcript via `MixKeyAndHash`. Passwords, API keys, and human tokens are not Noise PSKs.

`psk0` inserts `psk` at the start of message 1; `pskN` for N>0 inserts it at the end of message N. Multiple PSKs are supplied in modifier/token order. After processing `psk`, a sender may encrypt only after it has sent its own fresh `e`; this prevents catastrophic PSK-derived key reuse.

PSKs and static key pairs must stay in one hash-algorithm domain and outside unrelated protocols. Provision/rotate them with explicit peer/version identifiers; redact them from configs, fixtures, traces, and crash output.

Zero-RTT encryption occurs in patterns where the initiator pre-knows responder key material. It does not imply replay resistance or final authentication strength. Restrict early payloads to replay-safe/idempotent data and commit negotiated versions/suites to prologue/authenticated transcript.

Fallback/Noise Pipes are compound protocols, not ordinary retry:
- attempt `IK` using cached responder static
- on responder decryption failure, instantiate supported `XXfallback`
- reverse initiator/responder roles
- carry Alice's initial `e` as the prescribed pre-message/semi-ephemeral input
- bind negotiation and distinguish full/zero-RTT/fallback cases safely

Library feature support varies; for example, an implementation may support revision 34 but omit fallback. Never emulate missing fallback by reusing a failed handshake state or ephemeral key outside the specified transition.
