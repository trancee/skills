# Queue verification

Build the queue core against a fake `GattTransport` whose submissions and callbacks are explicitly controlled; compile the Android adapter against API 33/37.

Deterministic invariants:
- accepted operation B is never submitted before A callback/reset
- synchronous rejection creates no in-flight wait and advances once
- callback mismatch/duplicate/stale epoch never completes current request
- identical operations have distinct IDs/results
- API 33 read value comes from callback snapshot; write result uses stored request plus status
- queued cancellation skips submission
- in-flight caller cancellation does not free slot before transport completion/reset
- timeout retires/close epoch and no queued operation runs on it
- disconnect/permission loss/service change fail/drain exactly once
- callback-at-timeout/CAS race has one winner and no double resume
- bounded request/notification overflow follows policy
- subscription waits for CCCD; notification does not complete operations
- reliable-write transaction excludes ordinary operations

Use virtual time for timeouts/retry policy; no sleeps. Randomize submit/callback/cancel order in stress tests while asserting the invariant and retaining reproducible seeds.

Real Android matrix: repeated identical reads/writes, no-response writes, MTU/discovery/CCCD, forced peripheral delay/disconnect, Bluetooth toggle, process owner cancellation, service changed, Android 12–17, representative OEMs. Trace operation ID/epoch/type/submission/callback/status/elapsed without address or values.

A fake test proves coordinator semantics; only device tests prove platform callback behavior.
