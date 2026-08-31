# Single-owner operation model

One connection epoch owns:
- lifecycle `CoroutineScope`/Job
- serial callback executor/dispatcher
- bounded request `Channel<Request<*>>`
- one worker coroutine
- one atomic/confined `InFlight?`
- bounded unsolicited notification/event stream
- current `BluetoothGatt` and discovered object graph

`Request` contains monotonic ID, epoch, operation payload copied at enqueue, expected callback discriminator/target, timeout, and caller reply. `InFlight` adds internal callback completion and submission timestamp.

Worker algorithm:
1. receive request
2. skip if caller reply already cancelled or epoch not ready
3. install `InFlight`
4. invoke Android once
5. if synchronous rejection, clear/fail and continue
6. await internal callback completion with timeout
7. validate callback status/result
8. clear by compare-and-set ID/epoch
9. complete caller reply if active
10. receive next request

A bounded channel expresses memory/backpressure. Capacity is product-specific; cancellation/connection reset drains stale work. `Channel.RENDEZVOUS` is truly unbuffered; `Channel.UNLIMITED` is not.

Use a parent-owned actor/worker—not one launched coroutine per public method. `withContext(Dispatchers.IO)` does not serialize or make callback APIs blocking. Confinement should match the explicit callback executor; heavy result processing happens downstream.

One in-flight slot makes correlation deterministic. Do not scan a completion map by UUID/value. Duplicated UUIDs and identical writes remain distinct via request ID and discovered object/instance context.
