---
name: kotlin-coroutines
description: "Designs, implements, tests, and troubleshoots Kotlin coroutines and Flow with structured concurrency. Use when choosing CoroutineScope, Job, dispatchers, launch or async composition, handling cancellation, timeouts or exceptions, building Flow pipelines, coordinating channels or shared state, using virtual-time coroutine tests, or diagnosing leaks, deadlocks and hangs. Don't use for threads or executors without coroutines, Reactive Streams without coroutine interop, UI lifecycle work unrelated to coroutine ownership, or generic Kotlin code with no suspension or concurrency."
compatibility: "Current kotlinx.coroutines 1.11.0 is built with Kotlin 2.2.20 and supports JVM, JS/Wasm web, and Native variants as published. Platform integrations require matching modules. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/coroutines-guide.html"
  sourceVersion: "kotlinx.coroutines 1.11.0@8564f65764d3d05893cec026c6e94250e2b23874; Kotlin Help build 1155"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T15:00:36+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T15:00:36+02:00"
---

# Kotlin coroutines

## Step 1: Establish the concurrency contract

1. DEFINE feature | cancellation/failure bug | Flow/channel pipeline | shared state | dispatcher boundary | lifecycle leak | test | migration.
2. IDENTIFY owner scope, parent Job, children, lifetime/end signal, dispatcher requirements, blocking calls, result/error consumer, backpressure/state semantics, platform, and dependency versions.
3. READ the current [coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html), exact API reference, and [release notes](https://github.com/Kotlin/kotlinx.coroutines/releases/latest) before version/API changes.
4. PRESERVE structured concurrency: every coroutine must have an owner that awaits or cancels it. Use `GlobalScope` only for a deliberate process-lifetime root with explicit opt-in and failure policy.
5. ROUTE build-only dependency/toolchain work to `kotlin-gradle`; route generic Kotlin behavior to `kotlin-development`.

Completion: scope owner, lifetime, success result, cancellation path, failure propagation, dispatcher, and platform are explicit.

## Step 2: Inspect dependencies and risk sites

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM coroutines modules/versions, core/test/platform integrations, Kotlin targets, scope/builders, dispatchers, Flow/channel/shared-state constructs, blocking calls, broad catches, `GlobalScope`, detached `Job`, and test scheduler usage. Treat reported sites as candidates; inspect enclosing functions/classes before claims.

Completion: every changed coroutine and dependency has an identified owner, caller, and test seam.

## Step 3: Choose the structured primitive

- scope ownership, cancellation, timeouts -> READ `references/scopes-cancellation.md`.
- dispatchers, composition, exception/supervision -> READ `references/dispatchers-exceptions.md`.
- Flow/StateFlow/SharedFlow -> READ `references/flow.md`.
- channels, Mutex, atomics, confinement, select -> READ `references/channels-shared-state.md`.
- runTest, virtual time, debugging -> READ `references/testing-debugging.md`.
- platform/reactive/future/UI modules -> READ `references/dependencies-interop.md`.

SELECT the smallest primitive matching semantics: suspend function for one result, `coroutineScope` for concurrent children, Flow for stream observation, Channel for coordinated send/receive ownership, StateFlow for current state, SharedFlow for broadcast events, Mutex/atomic/confinement for shared mutation.

Completion: primitive semantics match cardinality, ownership, buffering, replay, failure, and cancellation.

## Step 4: Implement ownership and composition

1. ACCEPT a caller scope or create a scope owned by a lifecycle object; cancel owned scopes when that lifecycle ends.
2. USE `coroutineScope` when sibling failure should cancel the group; use `supervisorScope` only when siblings are intentionally independent and each failure is consumed.
3. USE `launch` for completion-only work whose failure follows the parent; use `async` for a value and await every `Deferred` in the owning scope.
4. KEEP sequential suspend calls sequential unless independence and latency justify explicit concurrency.
5. NEVER replace the parent's Job by passing `Job()`/`SupervisorJob()` to a child builder; create supervision at the ownership boundary.

Completion: no orphan Job/Deferred remains and parent completion waits for intended children.

## Step 5: Make cancellation cooperative and resource-safe

1. PROPAGATE cancellation through normal suspend points or explicit `ensureActive`/`yield` in CPU loops.
2. RETHROW `CancellationException` after local cleanup; broad `Exception`/`Throwable` catches must not convert cancellation into success/retry.
3. RELEASE resources in `finally`; use `withContext(NonCancellable)` only for a bounded suspending cleanup that must complete.
4. WRAP interruptible JVM blocking calls in `runInterruptible`; move unavoidable blocking I/O to an injected appropriate dispatcher.
5. DESIGN timeout acquisition so asynchronously acquired resources are closed even if cancellation wins at the boundary.

Completion: cancellation stops work promptly, children/resources terminate, and no post-cancel state update occurs.

## Step 6: Define dispatcher and failure policy

1. INHERIT context by default; switch only around work with a real execution requirement.
2. USE Default for CPU work, IO for blocking JVM I/O, Main for UI state, and limited parallelism for bounded concurrency; inject dispatchers at testable boundaries.
3. CLOSE/reuse dedicated thread dispatchers; avoid `Unconfined` outside narrow event-loop/test semantics.
4. HANDLE ordinary child failures at the owning suspend/await boundary. Use `CoroutineExceptionHandler` only for uncaught root/supervised `launch` reporting, never recovery.
5. PRESERVE the first failure and inspect suppressed failures where the platform supports them.

Completion: execution placement, blocking policy, and every exception consumer are explicit.

## Step 7: Implement stream or shared-state semantics

1. Flow: define cold/hot lifecycle, collection owner, context boundary, buffer/backpressure, completion/error, replay, and cancellation.
2. Channel: define producer/consumer ownership, capacity/overflow, close/cancel owner, and fan-in/fan-out behavior.
3. Shared state: prefer immutability/message passing; otherwise use one atomic operation, `Mutex.withLock`, or coarse confinement matching the invariant.
4. EXPERIMENTAL APIs such as select require local opt-in and version-specific review.
5. Avoid a Channel when a cold Flow or StateFlow expresses ownership/state without manual closure.

Completion: slow consumer, no consumer, cancellation, close/completion, and producer failure behavior are specified.

## Step 8: Test deterministic contracts

1. ADD `kotlinx-coroutines-test` at the same version as core in test scope.
2. USE `runTest`; inject `TestDispatcher` so delays use one `TestCoroutineScheduler`.
3. TEST success, parent/child cancellation, sibling failure, timeout boundary, cleanup, Flow completion/error/backpressure, and state transitions relevant to the change.
4. USE `runCurrent`, `advanceTimeBy`, and `advanceUntilIdle` according to scheduling intent; never use real sleeps as synchronization.
5. PUT intentional infinite background work in `backgroundScope`; reset `Dispatchers.Main` after tests.
6. JS tests must immediately return `TestResult`/`runTest` result.

Completion: tests are deterministic, finish with no leaked jobs/uncaught exceptions, and fail on the plausible bug.

## Step 9: Diagnose hangs, leaks, and races

1. REPRODUCE with bounded test timeout and coroutine names.
2. INSPECT Job tree, suspended stack, owner scope, dispatcher starvation, blocking calls, channel waits, mutex ownership, and unawaited Deferred.
3. ENABLE `-Dkotlinx.coroutines.debug` or debug probes only for diagnosis; collect coroutine dump before cancellation destroys evidence.
4. FIX ownership/protocol root cause; do not increase timeout, add sleeps, swallow cancellation, or use an unbounded dispatcher as a workaround.
5. STRESS race-sensitive state with repeated controlled execution and platform-appropriate tools after deterministic tests.

Completion: original scenario no longer hangs/leaks/races and lifecycle termination is observed.

## Step 10: Verify and report

1. RUN narrow coroutine tests, owning module tests, then CI-equivalent checks.
2. EXERCISE actual runtime path for cancellation/failure/dispatcher behavior; compilation alone is insufficient.
3. VERIFY dependency modules/versions and platform-specific Main/reactive/future integration.
4. COPY `assets/coroutine-report.md`; fill ownership tree, dispatchers, result/failure/cancellation, stream/state semantics, dependency versions, tests/runtime evidence, debug evidence, and limitations.

## Error Handling

- Test hangs -> inspect active children/scheduler/backgroundScope/foreign dispatcher; no larger timeout first.
- Cancellation is swallowed -> isolate broad catch and rethrow `CancellationException` before error mapping/retry.
- `CoroutineExceptionHandler` does not run -> child or async exceptions are consumed by parent/Deferred; handle at owner/await boundary.
- Flow invariant violation -> emit in one context or use `flowOn` for upstream; use `channelFlow` only for concurrent emission.
- Main dispatcher missing -> add the platform Main module/runtime or inject/set/reset Main in tests.
- JVM thread remains alive -> close owned `ExecutorCoroutineDispatcher` and cancel its scope.
- Dependency linkage error -> align all kotlinx.coroutines modules to one version and verify Kotlin/platform compatibility.
