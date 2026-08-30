---
name: ksp
description: "Configures, authors, tests, migrates, and troubleshoots Kotlin Symbol Processing. Use when applying com.google.devtools.ksp, consuming processors on JVM, Android, or Multiplatform targets, implementing SymbolProcessorProvider or SymbolProcessor, traversing KS declarations, types, and annotations, generating Kotlin, Java, or resources, handling multi-round deferral, declaring isolating or aggregating dependencies, preserving incremental and build-cache behavior, migrating kapt or KSP1, or diagnosing generated-source, task, and provider failures. Don't use for compiler plugins that change semantics, expression or statement analysis, source rewriting, runtime reflection, Java-only processors without KSP support, or generic Gradle tuning."
compatibility: "Current KSP 2.3.11 is KSP2-only. Since KSP 2.3.0 its version is independent of Kotlin and KSP is a standalone tool over stable compiler APIs; verify the release against the project's Kotlin/KGP/AGP/Gradle tuple. KSP1 has been removed and is unsupported. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/ksp-overview.html"
  sourceVersion: "KSP 2.3.11 (google/ksp@c44fd9a91192679e07a1d905dda022796e32bbbe); Kotlin Help build 1155 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T22:40:37+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T22:40:37+02:00"
---

# Kotlin Symbol Processing

## Step 1: Define the processing contract

1. DEFINE consume processor | author processor | generated API change | incremental defect | multi-round dependency | JVM/Android/KMP target | kapt/KSP1 migration | task/provider failure.
2. IDENTIFY annotation/input symbols, generated files and package/names, owning modules, target compilations/variants, processor options, public API/ABI impact, downstream consumers, Kotlin/KSP/KGP/AGP/Gradle versions, and clean/incremental test matrix.
3. READ the current [KSP overview](https://kotlinlang.org/docs/ksp-overview.html), [latest release](https://github.com/google/ksp/releases/latest), and relevant branch reference before changing setup/API.
4. KEEP the boundary explicit: KSP reads declarations/types/annotations and generates files; it cannot inspect expression/statement bodies, modify source, or change language semantics.
5. ROUTE general Kotlin source to `kotlin-development`, build/toolchain ownership to `kotlin-gradle`, KMP hierarchy/targets to `kotlin-multiplatform`, and exact external API lookup to `kotlin-api-reference`.

Completion: inputs, outputs, processor/consumer owners, target configurations, round/incremental behavior, and verification artifacts are explicit.

## Step 2: Inspect current KSP wiring

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM applied plugin/version/aliases, KSP2/KSP1 properties, processor API dependencies, `ksp*` configurations, KMP/Android targets/variants, `ksp { arg(...) }` options, processor/provider/service registrations, generated outputs, dependency declarations, validation/deferral, resolution entry points, incremental settings/logs, kapt coexistence, and manual generated-source wiring.

Completion: every processor dependency maps to one intended compilation/task and every provider maps to one service entry.

## Step 3: Configure a consumer

READ `references/setup-consumers.md`.

1. APPLY `com.google.devtools.ksp` only to modules that run processors; use current KSP2 version independently from Kotlin, then verify their compatibility by build.
2. ADD processor artifacts to the exact configuration: `ksp`/`kspTest` for single-platform, Android variant configurations where required, and `ksp<Target>`/`ksp<Target>Test` for KMP.
3. AVOID global `ksp` in KMP; add each required target explicitly. Use `ksp.allow.all.target.configuration=true` only as a temporary migration diagnostic.
4. PASS stable processor options through `ksp { arg(key, value) }`; keep secrets and machine-specific absolute paths out of task inputs/generated files.
5. LET KSP register generated sources; remove manual `build/generated/ksp` source-set wiring unless an exact tool/version requirement proves it necessary.

Completion: only intended compilations run KSP, generated sources compile automatically, and task/configuration names match Gradle output.

## Step 4: Structure annotations and processor modules

1. KEEP runtime/source annotations in a small dependency usable by consumers; keep the processor implementation in a JVM-hosted artifact depending on `com.google.devtools.ksp:symbol-processing-api`.
2. IMPLEMENT one or more `SymbolProcessorProvider` classes that construct processors from `SymbolProcessorEnvironment`.
3. REGISTER every provider by fully qualified name in `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider`.
4. KEEP processor implementation/compiler internals off consumer runtime classpaths; publish annotations/runtime helpers separately when needed.
5. VERSION generated API/schema behavior deliberately; a processor upgrade can be a source/binary compatibility change for consumers.

Completion: provider discovery, artifact/classpath boundaries, and generated API versioning are deterministic.

## Step 5: Discover and validate symbols

READ `references/processor-api.md`.

1. START from `Resolver.getSymbolsWithAnnotation()` or another narrow root API; use `getAllFiles()` only when the output truly depends on all files.
2. FILTER cheap syntax/name/kind data before calling `resolve()`; type resolution is explicit and costly.
3. HANDLE null qualified/containing declarations, Java/Kotlin differences, type aliases, variance/star projections, nullability, error types, expect/actual, and local declarations according to the processor contract.
4. VALIDATE exactly the symbols/types required for generation. DEFER only source symbols whose missing/error information can be supplied by a later generated round.
5. REPORT user-actionable diagnostics with `KSPLogger` attached to the offending symbol where possible; reserve exceptions for processor defects.

Completion: accepted/rejected/deferred input behavior is specified for every supported declaration/type shape.

## Step 6: Generate files with correct ownership

READ `references/code-generation.md`.

1. DERIVE package/file/member names deterministically from stable symbol identity; escape identifiers and render types with tested Kotlin/Java syntax.
2. CREATE files only through `CodeGenerator`; generate each path once per processing invocation and close/use every stream.
3. DECLARE `Dependencies(aggregating = false, sources...)` for outputs affected only by stated roots; declare aggregating output when any member of a wider set can change it.
4. PASS every originating `KSFile` that contributes directly. Rely on KSP resolution tracing for transitive symbol dependencies instead of attaching unrelated files.
5. SORT symbols/members/imports before emission, normalize line endings/encoding, avoid timestamps/absolute paths/random IDs, and make identical inputs byte-identical.
6. GENERATE compilable typed code instead of reflection/string lookups; preserve visibility/generics/nullability/modifiers required by the contract.

Completion: output bytes/path and incremental ownership are stable and no stale/duplicate output survives source removal/change.

## Step 7: Handle multiple rounds and processor lifecycle

READ `references/rounds-incremental.md`.

1. PROCESS only symbols visible in the current round; return unprocessable source symbols from `process()` for the next round.
2. DO NOT cache/reuse `KSNode`, `KSType`, or resolution results across rounds; resolution can change after generated files appear.
3. KEEP stable processor-owned metadata keyed by immutable names/paths only, and prevent duplicate generation across rounds.
4. END deferral when requirements become available or emit a precise error; a no-new-files round terminates and remaining deferred symbols fail.
5. USE `finish()` only after successful processing and `onError()` for cleanup after errors; never publish partial aggregate state on failure.

Completion: generated-to-generated dependencies converge, unresolved inputs fail clearly, and processor state cannot leak stale symbols across rounds.

## Step 8: Preserve incrementality and performance

1. KEEP `ksp.incremental=true` and build cache enabled in normal builds; disable only to isolate a reproduced defect.
2. CLASSIFY each output from its real dependency set—not desired performance. One global registry/schema is aggregating; per-symbol adapters are usually isolating.
3. MINIMIZE root queries/type resolution and avoid scanning classpath/packages without contract need.
4. REPRODUCE clean then incremental add/change/remove/rename cases; inspect `kspDirtySet.log`, `kspSourceToOutputs.log`, and dependency graph when results diverge.
5. TREAT Gradle-daemon heap/time as processor evidence in KSP2; profile only after output correctness/incrementality pass.

Completion: incremental outputs equal clean outputs byte-for-byte across the mutation matrix and unaffected work stays avoided.

## Step 9: Configure KMP and Android variants

READ `references/multiplatform-android.md`.

1. ADD the processor to each target/compilation that needs generated code; target name becomes configuration name without `Main` (`jvm` -> `kspJvm`).
2. ADD test/Android host/device/build-type/flavor processors only to their exact derived configurations.
3. USE `kspCommonMainMetadata` only when common metadata processing is the intended producer; verify how generated common output reaches each platform compilation.
4. ASSERT processor behavior/platform info for JVM, JS, Native, Wasm, and Android separately; a JVM run does not prove portable generated code.
5. RUN host-capable target tasks and record unavailable native targets rather than treating skipped tasks as passes.

Completion: each generated file is produced once in the correct source set/variant and compiles on every consuming target.

## Step 10: Test, migrate, and report

READ `references/testing-migration.md`.

1. TEST processor/provider discovery, options, diagnostics, generated bytes/API, compilation/runtime use, multiple rounds, clean/incremental equivalence, and source removal.
2. RUN the actual `ksp*` task followed by affected compile/test/package tasks; inspect generated files under the task's output directory.
3. MIGRATE kapt processor-by-processor only where the library supports KSP; remove that processor's kapt dependency/config and migrate changed generated APIs/callers.
4. MIGRATE from KSP1 to current KSP2; remove old `<kotlin>-<ksp>` versions and obsolete `ksp.useKSP2` toggles after verifying behavior differences.
5. COPY `assets/ksp-report.md`; fill versions, modules/configurations, providers/options, inputs/outputs, rounds, dependency classification, incremental matrix, diagnostics, and limitations.

Completion: clean/incremental/consumer tests pass, obsolete KSP/kapt/manual-generated-source paths are removed, and generated API changes are accounted for.

## Error Handling

- `ksp-… is too old for kotlin-…` -> select a current KSP2 release compatible with the Kotlin/KGP tuple; do not suppress the compatibility check.
- Processor never runs -> verify plugin application, exact `ksp*` configuration, processor artifact, provider service file path/content, and task dependencies.
- Provider not found -> package `META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` with the provider's fully qualified name and inspect the processor JAR.
- Generated symbol unresolved -> validate/defer the originating source symbol, return it from `process()`, and ensure a processor generates the dependency in a later round.
- `FileAlreadyExistsException`/duplicate output -> make generation identity stable and generate each path once across all rounds/processors.
- Incremental output stale/missing -> fix `Dependencies` roots/aggregating classification and resolution entry points; compare clean/add/change/remove logs.
- Processor sees no KMP target -> use `ksp<Target>` rather than global `ksp`, then verify derived configuration/task names.
- KSP2 OOM/debugging issue -> tune/debug the Gradle daemon (`org.gradle.jvmargs`, `-Dorg.gradle.debug=true`), not the removed compiler-daemon KSP1 path.
- Need expression body/source rewrite -> KSP cannot provide it; redesign around declarations/types or use a reviewed compiler plugin.
