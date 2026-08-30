# Scope ownership and cancellation

Sources: [coroutines basics](https://kotlinlang.org/docs/coroutines-basics.html) and [cancellation](https://kotlinlang.org/docs/coroutines-cancellation.html).

## Ownership

A scope combines context and Job. Parent completion waits for children; parent cancellation recursively cancels children. A non-cancellation child failure cancels its parent unless supervision defines independence.

- `coroutineScope`: suspend until block and children complete; child failure cancels siblings/parent scope
- `supervisorScope`: child failure does not cancel siblings; scope still waits; each child failure needs handling
- lifecycle-owned `CoroutineScope(SupervisorJob()+dispatcher)`: store and cancel at lifecycle end
- `GlobalScope`: process-lifetime root, delicate API, explicit rare policy only

Passing a new `Job()` into `launch`/`async` replaces inherited parent Job and detaches the child. Establish root/supervisor Job only where lifecycle ownership is created.

## Cancellation

Cancellation is cooperative and represented by `CancellationException`. kotlinx.coroutines suspend functions check it. CPU loops call `ensureActive()` for a check or `yield()` to check and allow peers to run.

```kotlin
try {
    work()
} catch (cancelled: CancellationException) {
    cleanup()
    throw cancelled
} finally {
    closeResource()
}
```

Use `cancelAndJoin` when the caller must observe termination. Use `awaitCancellation` for lifetime-bound workers.

`withContext(NonCancellable)` is for bounded suspending cleanup inside `finally`, not normal work. On JVM, `runInterruptible` bridges cancellation to interruptible blocking APIs.

## Timeouts

`withTimeout` cancels asynchronously and may race with return/resource acquisition. Return resources only through a pattern that closes them if timeout cancellation wins. Use `withTimeoutOrNull` only when `null` is the domain's timeout result; otherwise preserve a distinct timeout failure.
