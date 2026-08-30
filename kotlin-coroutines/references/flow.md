# Flow, StateFlow, and SharedFlow

Source: [Flows](https://kotlinlang.org/docs/coroutines-flow.html) and [API](https://kotlinlang.org/api/kotlinx.coroutines/).

## Choose semantics

- cold `Flow`: each collector starts an independent producer execution
- `StateFlow`: hot current-state holder, always has value, conflates updates by equality
- `SharedFlow`: hot broadcast with explicit replay/buffer/overflow; no intrinsic current state
- `channelFlow`: concurrent producers with channel-backed emission

Collection is suspending and owned by the collecting scope. `shareIn`/`stateIn` launch sharing in the supplied scope; that scope defines upstream lifetime and must be owned.

## Context

A `flow {}` emits from its collection context and must not use `withContext` to emit elsewhere. `flowOn(dispatcher)` moves only upstream of that operator. Downstream remains in collector context. Use `channelFlow` when concurrent child coroutines must send values.

## Backpressure and latest semantics

- default flow: sequential emitter/collector backpressure
- `buffer`: allows producer/consumer overlap with chosen capacity
- `conflate`: drops intermediate values, preserves latest
- `collectLatest`/`mapLatest`/`flatMapLatest`: cancel previous work when new value arrives
- `debounce`/`sample`: temporal selection, often experimental/version-sensitive

Choose dropping/cancellation only when intermediate values are semantically obsolete.

## Failure/completion

Flow exceptions are transparent. `catch` handles upstream exceptions before it, not downstream collector failures. Never catch cancellation as a value. `onCompletion` observes cause and can distinguish success/failure; `retry`/`retryWhen` need bounded policy, cancellation propagation, and idempotent upstream operation.

Hot flows do not complete merely because subscribers leave. Define sharing start policy, replay expiration, producer scope cancellation, and subscriber lifecycle.

## Testing

Collect under `runTest`; trigger producers and scheduler deterministically. For hot flows, start collectors before emissions when replay is zero. Assert dropped/replayed/latest behavior explicitly; cancel infinite collectors or launch them in `backgroundScope`.
