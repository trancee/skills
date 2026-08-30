# Writing trustworthy benchmarks

Source: [official writing guide](https://github.com/Kotlin/kotlinx-benchmark/blob/master/docs/writing-benchmarks.md).

## Annotation contract

- `@State`: required for multiplatform benchmark classes; non-JVM supports only `Scope.Benchmark`
- `@Setup` / `@TearDown`: public no-argument lifecycle methods; outside measured method time
- `@Benchmark`: public measured method; no arguments or one `Blackhole`
- `@BenchmarkMode`: Throughput or AverageTime cross-platform; JVM offers more JMH modes
- `@OutputTimeUnit`: display unit, not measurement precision
- `@Warmup` / `@Measurement`: iteration schedule
- `@Param`: nonempty string values converted to public mutable primitive/String state

Build profile values override annotation values.

## Optimizer defenses

Return one computed result; use `Blackhole.consume` for several values. A Blackhole prevents dead-code elimination but does not automatically prevent constant folding, loop hoisting, unrealistic branch prediction, or allocation removal. Construct representative mutable state in setup and verify generated/profiler behavior when results look impossible.

## Timed-boundary rules

- Move fixture generation, I/O, parsing, random input creation, and cleanup outside `@Benchmark` unless measured intentionally.
- Avoid sharing mutable state across invocations unless contention/state evolution is the subject.
- Reset state at the correct trial/iteration/invocation level; lifecycle level behavior is richer on JVM/JMH.
- Keep correctness assertions outside the hot path; validate equivalent outputs in ordinary tests.
- Parameterize real size/shape cases instead of extrapolating one tiny input.
- Benchmark end-to-end operation only when the question is end-to-end; otherwise isolate one operation and document excluded costs.

## JVM specifics

JMH generates subclasses; Kotlin benchmark classes/methods using state must be open, usually through all-open on `org.openjdk.jmh.annotations.State`. JVM-only benchmarks may use JMH annotations/scopes/forks/profilers, but cross-platform sources must stay within kotlinx-benchmark's common annotation subset.
