---
name: kotlin-multiplatform
description: "Designs, configures, migrates, tests, and publishes Kotlin Multiplatform projects. Use when choosing targets and source sets, applying hierarchy templates, sharing dependencies, introducing expect/actual or platform interfaces, configuring Android, JVM, JS, Wasm or Native compilations, running target tests, publishing root and target variants, or diagnosing source-set and variant-resolution failures. Don't use for single-platform Kotlin, Compose UI implementation, Apple framework or Objective-C interop, Gradle-only compiler and cache tuning, or platform application code unrelated to sharing."
compatibility: "Current Kotlin Multiplatform plugin 2.4.10 is fully supported with Gradle 7.6.3–9.5.0, AGP 8.5.2–9.1.0, and Xcode 26.4. Target build/test support depends on host. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/multiplatform/get-started.html"
  sourceVersion: "Kotlin 2.4.10; Kotlin Multiplatform Help build 554 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T15:40:43+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T15:40:43+02:00"
---

# Kotlin Multiplatform

## Step 1: Define the sharing contract

1. DEFINE new project | target/source-set change | shared API | expect/actual | dependency | test | publication | migration | resolution failure.
2. IDENTIFY products/modules, target platforms/architectures/environments, shared behavior, platform integrations, host matrix, publication consumers, Kotlin/Gradle/AGP/Xcode versions, and existing hierarchy/convention plugins.
3. READ the current [KMP start page](https://kotlinlang.org/docs/multiplatform/get-started.html), [project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html), and [compatibility guide](https://kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html) before target or version changes.
4. PRESERVE existing module boundaries, hierarchy template, target names, source-set names, publication coordinates, and integration methods unless the request changes them.
5. ROUTE compiler/cache/toolchain mechanics to `kotlin-gradle`; Apple framework/Objective-C boundaries to `kotlin-native-apple-interop`; source behavior to `kotlin-development`.

Completion: target matrix, host matrix, shared boundary, module owners, publication consumers, and version tuple are explicit.

## Step 2: Inspect project structure

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM KMP plugin/version, wrapper/AGP, targets/environments, source-set directories, hierarchy/dependsOn edges, dependencies, expect/actual declarations, platform imports in shared code, tests, publications, and host-disabled targets. Then run `./gradlew projects` and `./gradlew tasks --all`.

Completion: every source set maps to target compilations, dependencies, tests, and publication variants.

## Step 3: Choose modules, targets, and source sets

READ `references/project-model.md` and `references/hierarchy-expect-actual.md`.

1. DECLARE only shipped/tested targets; target declarations define produced artifacts and allowed APIs.
2. PLACE code in the narrowest source set shared by all intended targets: common, intermediate, or leaf platform.
3. USE the default hierarchy template for standard combinations; manual `dependsOn` only for a real unsupported sharing group.
4. SPLIT multiple similar target implementations into separate Gradle projects instead of low-level attributes in one project.
5. Keep device/simulator/native architecture targets distinct while sharing logic in generated intermediate sets such as `iosMain`/`appleMain`.

Completion: each source file's source set exactly matches its required platform APIs and consumers.

## Step 4: Bridge platform behavior

1. PREFER regular common interfaces plus injected platform implementations/factories.
2. USE expect/actual when common code must directly name a platform declaration and injection is not the better seam.
3. REQUIRE same package/kind/name and compatible signature for each expect/actual pair.
4. PLACE an actual in the highest intermediate source set serving all matching leaves.
5. PREFER expected functions/properties/interfaces/factories over expected classes; expected classes remain Beta and need explicit acceptance.

Completion: every expect has one effective actual for every target, with platform code absent from common source.

## Step 5: Configure dependencies and compilations

READ `references/dependencies-compilations.md`.

1. ADD a multiplatform dependency once to the narrowest shared source set using its base artifact.
2. ADD platform-only dependencies only to matching platform/intermediate source sets.
3. SELECT `api` only when dependency types cross the published API; otherwise use `implementation`.
4. CONNECT custom source sets/compilations explicitly; `associateWith` grants outputs and internal visibility and must be intentional.
5. VERIFY the effective variant for every target; one successful JVM resolution does not prove Native/JS/Wasm variants exist.

Completion: every dependency publishes/resolves the required variants and no platform artifact leaks into common metadata.

## Step 6: Configure and run tests

READ `references/testing.md`.

1. PUT shared contract tests in `commonTest` with `kotlin.test`.
2. PUT platform behavior/framework tests in corresponding platform/intermediate test sets.
3. RUN target-specific tasks first, then aggregate tasks only on a host capable of those targets.
4. TEST expect/actual behavior on each actualized target, not only the common API.
5. RECORD host-disabled target tests explicitly; never convert a skipped target into a pass.

Completion: every published target has behavioral test evidence from a capable host or an explicit gap.

## Step 7: Build and publish artifacts

READ `references/publishing.md`.

1. APPLY `maven-publish` at the owning library module and preserve group/artifact/version policy.
2. PUBLISH root `kotlinMultiplatform` metadata plus every target-specific publication from one host/workflow.
3. PUBLISH to a local/disposable repository first and resolve a real consumer for each target.
4. CONFIGURE Android publication explicitly; KMP does not publish Android artifacts by default.
5. VERIFY sources/docs, Gradle module metadata links, target coordinates, signatures/checksums, and repository duplicate policy.

Completion: root metadata resolves every supported target artifact in real consumers.

## Step 8: Migrate or extend a project

1. ADD one target at a time; compile common code and expose invalid platform dependencies before adding leaf implementation.
2. MOVE shared code upward only when all newly labeled targets support every API/dependency.
3. REMOVE manual hierarchy edges covered by the default template or explicitly reapply the template before custom additions.
4. MIGRATE deprecated Android target/withJava/legacy hierarchy/bitcode/similar-target patterns using `references/migration-troubleshooting.md`.
5. SEPARATE structural migration from product behavior changes.

Completion: no deprecated/parallel hierarchy remains and the expanded matrix compiles/tests/publishes.

## Step 9: Diagnose failures

READ `references/migration-troubleshooting.md`.

1. CLASSIFY plugin/version | hierarchy | unavailable API | missing actual | dependency variant | host-disabled target | compilation/link | publication metadata.
2. RUN the narrow target/source-set compile or dependency report.
3. TRACE failure upward through leaf -> intermediate -> common source sets and dependency metadata.
4. FIX the first ownership/variant/version boundary; never copy platform code across leaves or force incompatible artifacts as a shortcut.
5. RE-RUN the target task, affected peers, aggregate tests, and consumer resolution.

Completion: original failure is removed at its structural cause across all affected targets.

## Step 10: Verify and report

1. COMPILE common metadata and every affected target on capable hosts.
2. RUN shared and platform-specific tests.
3. INSPECT source-set hierarchy and effective dependencies.
4. BUILD/publish target artifacts and resolve local consumers when publication changes.
5. COPY `assets/multiplatform-report.md`; fill versions, modules, target/host matrix, hierarchy, expect/actual, dependencies, tests, publications, migration, and limitations.

## Error Handling

- Platform API in common source -> move to matching source set or introduce common interface plus platform implementation.
- Missing actual -> add compatible actual in each leaf or suitable intermediate source set; do not suppress expect/actual diagnostics.
- Default hierarchy not applied -> remove unnecessary manual dependsOn edges or explicitly reapply/disable the template and own the full graph.
- Dependency resolves on one target only -> verify module metadata/platform variants and relocate dependency to supported source set.
- Similar targets fail/deprecate -> split implementations into separate Gradle projects rather than custom attributes in one project.
- Native/Apple task disabled -> run on compatible host; warning suppression does not make the target verified.
- Root publication exists but consumer fails -> publish every target artifact and inspect root `.module` references.
- Duplicate publication rejected -> publish all coordinates from one host/workflow only.
