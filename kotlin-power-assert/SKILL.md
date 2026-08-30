---
name: kotlin-power-assert
description: "Configures, uses, debugs, and exposes Kotlin Power-assert integrations. Use when applying the Power-assert compiler plugin in Gradle, Maven, JVM, or Multiplatform builds; selecting transformed functions or compilations; interpreting expression-value diagrams; authoring @PowerAssert assertion APIs, soft assertions, or CallExplanation renderers; and diagnosing missing transformations or runtime intrinsic failures. Don't use for general Kotlin tests, assertion-library selection without Power-assert, compiler-plugin implementation, or non-Kotlin assertions."
compatibility: "Power-assert is Experimental in Kotlin 2.4.10. Keep the compiler plugin, Kotlin compiler, Gradle plugin, Maven plugin artifact, and runtime library on one Kotlin version. Kotlin 2.4.10 selects source sets with includedSourceSets; compilationFilter exists only in later source and must be version-gated. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/power-assert.html"
  sourceVersion: "Kotlin 2.4.10; Kotlin Help build 1155 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T17:43:53+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T17:43:53+02:00"
---

# Kotlin Power-assert

## Step 1: Define the diagnostic contract

1. DEFINE enable plugin | select function | select compilation | improve assertion expression | author assertion API | soft assertions | Maven integration | migration | missing diagram | intrinsic failure.
2. IDENTIFY modules, Kotlin targets/compilations, build system, Kotlin/KGP version owner, assertion functions and overloads, test/runtime source sets, library consumers, and expected failure output.
3. READ the current [Power-assert guide](https://kotlinlang.org/docs/power-assert.html), [component stability](https://kotlinlang.org/docs/components-stability.html), and Kotlin release/migration notes before adoption or upgrade. Power-assert is Experimental; obtain explicit acceptance for production/library API reliance.
4. PRESERVE the repository's plugin/version ownership, test framework, assertion semantics, source-set hierarchy, and failure type unless the request changes them.
5. ROUTE general build/toolchain work to `kotlin-gradle`, source/test behavior to `kotlin-development`, and target/source-set design to `kotlin-multiplatform`.

Completion: owning module, transformed compilations/functions, failure semantics, stability acceptance, version owner, and proof command are explicit.

## Step 2: Inspect current integration

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM Gradle/Maven plugin application, Kotlin and Power-assert versions, `powerAssert` options, transformed functions, source-set/compilation selectors, runtime dependencies, annotated APIs, explanation consumers, assertion call sites, and production-source instrumentation.

Completion: static configuration and every relevant call site are mapped to the compilation that compiles it.

## Step 3: Apply the compiler plugin

READ `references/setup-gradle-maven.md`.

1. APPLY `kotlin("plugin.power-assert")` or `org.jetbrains.kotlin.plugin.power-assert` to each module compiling transformed call sites.
2. ALIGN its version exactly with the module's Kotlin compiler/plugin version; keep one version owner.
3. KEEP the default selection of all test source sets for test-only diagnostics.
4. ENABLE main/custom source sets only when their assertion diagnostics are required and runtime/deployment impact is accepted.
5. USE the Maven compiler plugin plus `kotlin-maven-power-assert` dependency for Maven builds.

Completion: the plugin artifact loads on each intended compilation with one aligned Kotlin version.

## Step 4: Select functions and compilations

READ `references/configuration.md`.

1. KEEP `kotlin.assert` as the default unless another assertion function is used.
2. ADD exact fully-qualified callable names through `functions`; configuration is a set, not an overload signature matcher.
3. OMIT `@PowerAssert`-annotated functions from `functions`; the annotation makes calls discoverable when the caller's compilation has the plugin.
4. ON Kotlin 2.4.10, set `includedSourceSets` to exact source-set names; use `compilationFilter` only after the target Kotlin version's released API documents it.
5. CONFIRM every configured function has a supported Boolean condition plus final `String`/message-lambda shape before relying on transformation.

Completion: each intended call is selected once and each unintended compilation remains untransformed.

## Step 5: Write diagnostic assertions

1. KEEP the causal expression inside the transformed call; precomputed Boolean variables hide their subexpressions.
2. USE stable values and side-effect-free predicates so captured intermediate values explain one evaluation clearly.
3. RETAIN meaningful custom messages; Power-assert appends expression context rather than replacing domain intent.
4. USE `require`/`check` for always-enforced preconditions/invariants. Treat `kotlin.assert` according to platform assertion-enable semantics; Power-assert does not turn disabled assertions into enforcement.
5. VERIFY null, short-circuit, property getter, collection, string, and multiline rendering cases relevant to the assertion.

Completion: a deliberate failure shows the failing expression and the values needed to identify its cause without changing assertion semantics.

## Step 6: Author Power-assert-capable APIs

READ `references/library-integration.md`.

1. APPLY the compiler plugin to the library module and retain/add its runtime dependency.
2. OPT IN narrowly to `ExperimentalPowerAssert`, MARK the assertion function with `@PowerAssert`, and mark message/builders or sensitive/noisy parameters/types with `@PowerAssert.Ignore`.
3. ACCESS `PowerAssert.explanation` only inside an annotated function.
4. HANDLE a nullable explanation and preserve the library's existing failure type, contracts, soft-collection behavior, and message policy.
5. TEST both a plugin-enabled consumer and the documented non-transformed fallback path.

Completion: published annotation/runtime metadata lets enabled consumers transform calls while library behavior remains intentional without call transformation.

## Step 7: Implement soft assertions or custom rendering

1. COLLECT failures instead of throwing inside the soft scope, then throw one aggregate failure after the block.
2. READ `CallExplanation.arguments` in parameter order; handle `null` for implicit/default/ignored arguments.
3. SLICE source with `startOffset` inclusive and `endOffset` exclusive.
4. USE `toDefaultMessage()` unless a stable custom renderer is required; custom renderers must tolerate new expression shapes across Experimental upgrades.
5. REGISTER unannotated collector functions or annotate owned ones, then verify multiple failures appear in deterministic order.

Completion: all expected failures and expression diagrams appear once in one aggregate result.

## Step 8: Diagnose missing or broken output

READ `references/troubleshooting.md`.

1. CLASSIFY plugin not applied | version mismatch | compilation excluded | callable name mismatch | unsupported function shape | precomputed expression | assertions disabled | runtime missing | intrinsic access | renderer defect.
2. RUN the narrow compile/test/application task with one deliberate failure.
3. CHECK the call site's owning module and compilation, not only the assertion library module.
4. FIX the first configuration/runtime boundary; do not replace diagnostic evidence with hand-built message duplication.
5. RE-RUN the deliberate failure, then the affected test suite with the deliberate failure restored to passing.

Completion: the original assertion path emits the expected diagram and the normal suite passes.

## Step 9: Verify and report

1. COMPILE every transformed target/compilation.
2. RUN a deliberate failing assertion and capture exception type, custom message, source expression, and intermediate values.
3. RUN normal tests after removing/reversing the deliberate failure.
4. VERIFY plugin-disabled/fallback behavior for published assertion APIs.
5. COPY `assets/power-assert-report.md`; fill versions, configuration, functions, compilations, failure evidence, runtime API, and Experimental limitations.

## Error Handling

- Plugin ID unresolved -> align repositories/plugin management and use the Kotlin plugin's exact version.
- No value diagram -> inspect caller module, source-set/compilation selection, exact fully-qualified function name, supported shape, and expression structure.
- `NotImplementedError` from `PowerAssert.explanation` -> apply/align the plugin where the annotated function is compiled and verify the runtime dependency; never call the intrinsic from an unannotated function.
- Gradle Experimental warning -> add the narrow documented `ExperimentalKotlinGradlePluginApi` opt-in around the DSL after accepting stability; do not suppress all compiler warnings.
- Gradle selector unresolved -> use `includedSourceSets` on Kotlin 2.4.10; adopt `compilationFilter` only with a released Kotlin version that provides it, then verify every intended target compilation.
- JVM `assert` does not fail -> enable assertions for that runtime/test task or use `require`/`check` when enforcement must be unconditional.
- Maven transforms nothing -> configure both `<compilerPlugins><plugin>power-assert</plugin>` and the matching `kotlin-maven-power-assert` plugin dependency.
- Library consumer fails at runtime -> test plugin-enabled and fallback consumers; align `kotlin-power-assert-runtime` with the compiler plugin.
