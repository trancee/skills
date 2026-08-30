# Dispatchers, composition, and exceptions

Sources: [context/dispatchers](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html), [composition](https://kotlinlang.org/docs/composing-suspending-functions.html), and [exceptions](https://kotlinlang.org/docs/exception-handling.html).

## Dispatchers

- inherit: preserve caller context by default
- `Dispatchers.Default`: CPU-bound shared pool
- `Dispatchers.IO`: JVM blocking I/O pool; not a substitute for cancellable APIs
- `Dispatchers.Main`: UI/event-loop module required
- `limitedParallelism(n)`: bound concurrency without owning threads
- `Dispatchers.Unconfined`: resumes according to suspending function; narrow expert/test use
- `newSingleThreadContext`/executor dispatcher: expensive owned resource; close or reuse

Inject dispatchers into components that must switch contexts. `withContext` changes context for one suspendable region and returns to caller context.

## Composition

Suspend calls are sequential by default. Use sibling `async` inside `coroutineScope` only for independent value-producing operations, and await each Deferred. Lazy async starts on `start`/`await`; sequential awaits without starting both lose concurrency.

`launch` returns Job for completion; `async` captures result/failure in Deferred. An unawaited Deferred hides both result and exception.

## Exceptions

- child failure propagates to parent; parent handles only after children terminate
- root `launch` reports uncaught failure; root `async` stores it until await
- `CoroutineExceptionHandler` observes uncaught root/supervised launch failures after completion; it cannot recover
- handler on an ordinary child or async has no recovery effect
- first exception wins; later failures may be suppressed on supported platforms
- cancellation exceptions are transparent/ignored by handlers and must be rethrown when caught

Supervision changes upward failure propagation, not cancellation from parent to children. Direct supervised children need independent exception handling/awaiting.
