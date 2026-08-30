# Pattern and suite selection

Normative source: [Noise revision 34 Sections 7, 12, and 14](https://noiseprotocol.org/noise.html).

Pattern characters describe static-key status: `N` none, `K` pre-known, `X` transmitted later under encryption, and initiator-only `I` transmitted immediately with reduced identity hiding.

Common interactive choices:

| Pattern | Prior knowledge | Authentication after completion | Key caveat |
|---|---|---|---|
| `NN` | none | neither peer | encryption without identity authentication |
| `NK` | initiator knows responder static | responder to initiator | first payload can be 0-RTT/replayable; initiator unauthenticated |
| `NX` | none | responder to initiator | responder static transmitted during handshake |
| `XN` | none | initiator to responder | responder unauthenticated |
| `XK` | initiator knows responder static | mutual | responder identity pre-known; initiator static transmitted later |
| `XX` | none | mutual after static-key policy | general interactive choice; no first-message peer authentication |
| `IK` | initiator knows responder static | mutual | initiator static sent immediately; weaker identity hiding and 0-RTT replay concerns |
| `KK` | both statics pre-known | mutual | provisioning/rotation must bind both keys |

This table is a routing aid, not a substitute for revision-34 payload and identity-hiding tables. Inspect each handshake payload's source/destination grade before sending secrets or actions. `XX` authenticates possession of exchanged static keys only after the application accepts those keys.

One-way `N`, `K`, and `X` produce transport only sender->recipient; discard the reverse `CipherState`.

Prefer named fundamental patterns. Deferred patterns are the unstable portion of revision 34. Pattern extensions, hybrid/KEM schemes, signatures, and custom tokens need their own specification and expert analysis.

Official suites:
- DH: `25519`, `448`
- cipher: `ChaChaPoly`, `AESGCM`
- hash: `SHA256`, `SHA512`, `BLAKE2s`, `BLAKE2b`

`448` should pair with a 512-bit hash. `AESGCM` requires constant-time/hardware support and its revision-34 per-key data-volume limit. Protocol names are ASCII, at most 255 bytes, with exact case and modifier ordering.
