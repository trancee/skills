# kotlinx-benchmark troubleshooting

## No task or benchmark

- confirm plugin resolves through Gradle Plugin Portal
- confirm runtime resolves through Maven Central and matches plugin version
- confirm registered target name equals Kotlin target/compilation/default source-set name
- list `*Benchmark*` tasks; use full module path
- confirm source belongs to the registered compilation
- confirm public `@Benchmark` method and class/state requirements
- inspect profile include/exclude regex against fully qualified names

## JVM

- generated subclass/final error: apply matching all-open plugin for `org.openjdk.jmh.annotations.State` or use explicit `open`
- no JMH classes: runtime/source-set dependency misplaced or benchmark compilation not associated
- fork failure/lock: inspect JDK, `jvmForks`, `jmhIgnoreLock`, process permissions, and JMH version
- profiler: build `<target>BenchmarkJar`, run `java -jar ... -h`, then verify profiler availability separately
- one project cannot safely register multiple JVM targets with different JMH versions

## JS/Wasm

Verify Node target/runtime and executable. For built-in JS executor, inspect `jsUseBridge`; for default executor, inspect benchmark.js packaging. Wasm must use the exact Kotlin version supported by the kotlinx-benchmark release when required.

## Native

Only host targets execute. Confirm native target name, compiler availability, and release/debug build type. Cross-host results are not directly comparable. `nativeFork=perIteration` increases isolation and startup cost; `nativeGCAfterIteration` changes measured environment.

## Bad measurements

- implausibly fast: dead-code/constant elimination, tiny constant input, hoisted work
- steadily improving: insufficient warmup/JIT or cache buildup
- steadily degrading: thermal throttling, GC/state growth, resource leak
- high variance: shared host, short iterations, I/O/scheduling, mixed workloads
- changed result count: include regex, parameters, target/source set, code-generation failure
- output missing/invalid: report format/path, task failure, stale build output

Fix benchmark correctness and execution before increasing iteration counts.
