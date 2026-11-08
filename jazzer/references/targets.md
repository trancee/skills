# Targets, mutation and meaningful oracles

Sources: [released mutation framework](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/docs/mutation-framework.md), [FuzzTest source](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/src/main/java/com/code_intelligence/jazzer/junit/FuzzTest.java), [lifecycle](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/src/main/java/com/code_intelligence/jazzer/junit/Lifecycle.java), [libFuzzer targets](https://llvm.org/docs/LibFuzzer.html#fuzz-target).

## 1. Select the consumer boundary

1. Pick a narrow entry point with meaningful input-dependent behavior: parser/decoder, protocol message, authorization decision, normalization or a stateful API operation sequence. Reach real implementation code, not mock echoes or a target that only consumes input.
2. Define the invariant before fuzzing: round-trip semantics for supported values, differential agreement with an independent implementation, ordering plus multiplicity, bounds/resource guarantees, or a security property. Do not demand byte-for-byte equality after a deliberately lossy/canonicalizing conversion.
3. Handle only documented expected invalid-input failures around the operation that can reject input. Keep assertions and subsequent operations outside that catch. Do not blanket-catch Throwable/Exception/RuntimeException, ignore all failures, or exclude a real defect just to continue fuzzing.
4. Avoid host side effects: isolate files/network/processes, use no live credentials or production services. Bound expensive inputs and operations while retaining the failure-relevant domain. Join spawned threads and reset global/cache state deterministically between invocations.

## 2. Choose an input representation

| Shape | Use | Corpus consequence |
|---|---|---|
| Single `byte[]` | Raw binary/text parser, maximum direct byte fidelity | Legacy raw-byte path; typed mutator framework is not used |
| Single `FuzzedDataProvider` | Multiple values derived from raw bytes with explicit consumption | Replay requires same consumption order/bounds, not just decoded text |
| Supported typed parameters | Strings, primitives, arrays, lists/maps, enums, records, beans, builders, protobuf messages | Structured serialization; corpus files are not generally literal input strings or JSON |

- Supported types are finite and version-specific; "any parameters" in examples is not permission to pass arbitrary runtime classes. No available mutator -> choose a supported DTO/record/primitive boundary or raw/provider adapter that still reaches real code.
- Reference types may be null. Use `@NotNull` only for the documented non-null domain; apply to nested type arguments or `constraint=PropertyConstraint.RECURSIVE` when needed. Test invalid/null acceptance separately if it is part of the API contract.
- Use `@InRange`, `@WithUtf8Length`, `@WithSize`, `@Finite` and other supported annotations to guide practical input domains. The mutation docs describe constraints as best-effort; they are generation guidance, not application validation or authorization. Length is UTF-8 bytes where the annotation says so, not Java character count.
- `@ElementOf` feeds a fixed constant set; `@ValuePool` supplies static `Stream<?>` values or file patterns and can apply further mutations. Distinguish dictionaries for raw bytes, value pools for typed values, and actual regression seeds.
- Classes built by the cached constructor mutator without getters may not serialize for `@MethodSource`; startup warnings can indicate ignored seeds. Do not count an ignored seed as exercised. Preserve versions/signatures and replay saved entries after upgrades.

## 3. Keep the lifecycle deterministic

- Default `@FuzzTest` lifecycle is `PER_TEST`: before/after-each hooks are not invoked for every fuzz iteration. Use explicit per-invocation state reset, or supported `Lifecycle.PER_EXECUTION` when test instance/extensions require it; this trades throughput for reset semantics.
- Regression mode uses the full lifecycle per input. A crash dependent on leftovers may fail to replay alone; minimize state into the serialized operation sequence rather than hiding nondeterminism.
- Read published annotations and logs against the pinned release source: generated Javadoc prose can lag implementation (for example directory conventions and truthy environment flags). JUnit fuzzing runs one selected fuzz method; separate targets belong in separate invocations.

## 4. Use the runnable probes correctly

- `assets/Base64Target.java`: standalone raw decoder example. Invalid Base64 is rejected narrowly; successfully decoded bytes survive canonical encode/decode. It demonstrates a meaningful invariant, not a defect claim about the JDK.
- `assets/SortFuzzTest.java`: structured `List<Integer>` input with explicit seeds, ordering and multiset-preservation oracles. It checks duplicates/extreme values without a tautological size-only assertion. The companion `assets/pom.xml` is a disposable Maven consumer, not a replacement for a project's build conventions.
- Adapt the target to the requested application and exercise its actual boundary. Probes do not imply application fuzz coverage. For Kotlin/JVM, use the Java integration and Kotlin's actual generated class/type-use metadata; verify `@JvmStatic` when exposing a static standalone entry point. Kotlin/Native and Android device/ART setup are outside this JVM recipe.

DONE: the input reaches real behavior, the oracle can catch a plausible consumer-visible defect, malformed inputs are classified deliberately, and iterations remain bounded, isolated and reproducible.
