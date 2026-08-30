# Channels and shared state

Sources: [Channels](https://kotlinlang.org/docs/channels.html), [shared state](https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html), and [select](https://kotlinlang.org/docs/select-expression.html).

## Channels

A Channel coordinates suspending send/receive. Define:
- element ownership
- capacity (`RENDEZVOUS`, bounded, conflated, unlimited) and overflow
- number of producers/consumers
- who closes normally
- who cancels on abandonment/failure
- whether remaining buffered elements drain

Producer completion should close its send side. Consumer abandonment should cancel upstream when it owns the pipeline. `consumeEach` cancels the channel on completion/failure and is unsafe for independent fan-out consumers; use `for (value in channel)` when peers must continue.

Prefer Flow for observable cold pipelines and StateFlow for current state. Use Channel when explicit queue/rendezvous/multi-party send-receive protocol is the contract.

## Shared mutation

`volatile` does not make compound operations atomic. Choose:
- atomic/thread-safe structure for a simple linearizable operation
- `Mutex.withLock` for suspending mutual exclusion around an invariant
- coarse thread/dispatcher confinement for owned complex state
- actor/channel ownership for serialized commands
- immutable StateFlow updates for observable state

Never hold a blocking JVM lock across suspension. Keep Mutex critical sections small and avoid calling unknown suspending code while holding ownership unless protocol demands it.

## Select

`select` waits for the first available clause and is experimental. Selection is biased toward the first ready clause. Handle channel closure with `onReceiveCatching`; a closed clause can become immediately selectable. Test simultaneous readiness, cancellation, and closure ordering at the exact library version.
