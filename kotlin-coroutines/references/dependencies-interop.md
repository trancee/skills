# Dependencies, platforms, and interop

Source: [kotlinx.coroutines README](https://github.com/Kotlin/kotlinx.coroutines).

Keep all kotlinx.coroutines modules on one version. Current 1.11.0 is built with Kotlin 2.2.20.

- `kotlinx-coroutines-core`: common builders, Job/Deferred, Flow, Channel, Mutex, Semaphore
- `kotlinx-coroutines-test`: runTest/TestScope/TestDispatcher; test scope only
- `kotlinx-coroutines-debug`: DebugProbes/JUnit timeout tools; JVM diagnostics
- `kotlinx-coroutines-android`: Android Main dispatcher and uncaught reporting
- JavaFX/Swing modules: platform Main dispatcher
- `kotlinx-coroutines-slf4j`: MDCContext propagation
- `kotlinx-coroutines-jdk8`, Guava, Play Services: future/task await bridges
- reactive/reactor/rx2/rx3 modules: Reactive Streams integrations

KMP common code depends on base `kotlinx-coroutines-core`; Gradle resolves platform variants. Add platform-specific modules only to platform source sets.

JVM-only `Dispatchers.IO`, interruptible blocking, executors, CompletableFuture, and thread-local integrations are unavailable to common code. Web provides Promise integration; 1.11.0 moved Promise APIs to the web target and Wasm/JS now accepts only `JsAny` subtypes.

Interop adapters carry cancellation semantics in both directions only as documented. Verify whether cancelling coroutine cancels future/subscription/task and vice versa. MDC/thread-local context must use a `ThreadContextElement`; thread names/locals do not follow suspension automatically.

Use API annotations at the exact version. Stable, experimental, obsolete, internal, and deprecated APIs have different guarantees; stale narrative compatibility pages do not override current declaration annotations.
