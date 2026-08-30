# Coroutine testing and debugging

Source: [kotlinx-coroutines-test](https://github.com/Kotlin/kotlinx.coroutines/tree/master/kotlinx-coroutines-test).

## Test dependencies and scope

Add `kotlinx-coroutines-test` at the same version as core to test source sets only. `runTest` skips scheduler-controlled delays, surfaces uncaught child failures, and defaults to a 60-second real timeout.

Use one `TestCoroutineScheduler` across injected `StandardTestDispatcher`/`UnconfinedTestDispatcher` instances. Dispatchers.IO/Default used directly do not share virtual time; inject dispatchers for deterministic delay tests.

- `runCurrent()`: run work scheduled at current virtual time
- `advanceTimeBy(d)`: advance toward a boundary; understand whether boundary tasks run
- `advanceUntilIdle()`: drain scheduled work
- `currentTime`: virtual time
- `backgroundScope`: intentional infinite workers, cancelled when test ends

`StandardTestDispatcher` queues work predictably. `UnconfinedTestDispatcher` eagerly enters top-level children until first suspension; use only when that scheduling contract is intended.

On JS, return the `runTest`/`TestResult` immediately from the test function. If overriding Main, call `Dispatchers.resetMain` and close any owned real dispatcher in teardown.

## Contracts to test

- parent waits for children
- child failure cancels siblings under coroutineScope
- supervised siblings remain independent and failures are consumed
- cancellation reaches CPU/blocking work and cleanup runs
- timeout/resource race
- Deferred is awaited
- Flow collection/error/backpressure/latest/replay behavior
- channel close/cancel and blocked sender/receiver

## Debugging

Name coroutines with `CoroutineName`. JVM `-Dkotlinx.coroutines.debug` adds coroutine IDs to thread names. IDEA Coroutine Debugger or `kotlinx-coroutines-debug` DebugProbes can dump active/suspended coroutines. Capture dump before cleanup/cancellation changes state. Debug probes add overhead and are diagnostic, not production defaults.
