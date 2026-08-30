---
name: kover
description: "Configures, verifies, and troubleshoots Kotlinx Kover coverage for JVM, Android, and Kotlin Multiplatform projects. Use when adding Gradle or Maven Kover, aggregating multi-module coverage, filtering reports, enforcing line, branch, or instruction thresholds, choosing the IntelliJ or JaCoCo engine, merging binary reports, or diagnosing instrumentation gaps. Don't use for JavaScript or Native coverage, Android device tests, non-JVM coverage, or generic test writing without Kover."
compatibility: "Measures JVM bytecode. Gradle path requires Gradle 6.8.3+; Android requires AGP 7+; Maven path requires Maven 3+ and Java 8+. Helper requires Python 3.11+. Verify live requirements before version changes."
metadata:
  category: "development"
  source: "https://kotlin.github.io/kotlinx-kover/"
  sourceVersion: "Kover 0.9.9 (Kotlin/kotlinx-kover@95de3ac635494dc745ecc264344190a6c789abe8); published plugin docs examples 0.9.8"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T13:45:53+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T13:45:53+02:00"
---

# Kover

## 1. Scope+version

1. DEFINE Gradle | Maven | JVM agent | CLI/offline; single/multi-module; JVM/Android/KMP; report/threshold/instrumentation problem.
2. IDENTIFY test tasks, JVM classes, report variant, merging module, CI consumer, current Kover/Kotlin/Gradle/AGP/JDK versions, engine.
3. READ current [home](https://kotlin.github.io/kotlinx-kover/), selected integration page, and [latest release](https://github.com/Kotlin/kotlinx-kover/releases/latest). Published docs may lag release; use one verified version across plugin/artifacts/agent/CLI.
4. Kover measures JVM bytecode only: JVM tests and Android local unit tests. KMP JS/Native tests and Android device instrumentation tests are outside coverage.

## 2. Inspect

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```
CONFIRM plugin/version/modules, project types, `kover(project(...))`, engine, variants, filters, verification bounds, disabled test tasks/source sets, Maven goals, report paths. Discover wrapper tasks; use full task paths.

## 3. Establish coverage contract

1. RUN existing tests without Kover; preserve result.
2. DEFINE measured production classes, contributing test tasks/modules/variants, excluded generated/infrastructure code, metric (`LINE|INSTRUCTION|BRANCH`), aggregation (`COVERED|MISSED` count/percentage), grouping (`APPLICATION|CLASS|PACKAGE`), bound, report format/path.
3. Treat coverage as execution evidence, not test-quality proof. Never add low-value calls solely to increase percentage.
4. Start threshold from measured intentional scope; raise deliberately. Never weaken filter/bound or disable verification to pass unchanged code.

## 4. Configure integration

- Gradle -> READ `references/gradle.md`; preferred path
- filters/bounds/instrumentation -> READ `references/filters-verification.md`
- multi-module/variants/CI -> READ `references/multimodule-ci.md`
- Maven/agent/CLI/offline -> READ `references/other-integrations.md`

Gradle plugin:
```kotlin
plugins { id("org.jetbrains.kotlinx.kover") version "<KOVER_VERSION>" }
repositories { mavenCentral() }
```
Apply per project-type rules. Kover/JaCoCo dependencies resolve from Maven Central.

## 5. Reports+verification

1. Configure filters once at common/variant level; excludes win includes. Filters affect report+verification, not necessarily instrumentation.
2. Configure total or named report variant in merging module only.
3. Add named verification rule with explicit grouping/unit/aggregation/bound.
4. RUN exact task:
   - total: `koverHtmlReport`, `koverXmlReport`, `koverBinaryReport`, `koverLog`, `koverVerify`
   - named variant: suffix task with variant, e.g. `koverVerifyRelease`
5. Report tasks trigger included test tasks automatically. In multi-project builds, use full path (`:coverage:koverVerify`) to avoid unrelated project tasks.

## 6. Aggregate

1. Select merging module, usually root.
2. Apply Kover to participating modules; declare in merger:
   ```kotlin
   dependencies {
       kover(project(":moduleA"))
       kover(project(":moduleB"))
   }
   ```
3. Include every module whose classes or tests must contribute. A code-only module reports 0% alone if tests live elsewhere.
4. Use one engine across all `kover` dependencies. Mixed embedded Kover/JaCoCo is invalid.
5. Aggregated settings plugin is prototype only; do not choose for production by default.

## 7. Instrumentation failures

On-the-fly instrumentation can change test timing or fail bytecode verification. Reproduce with/without Kover. If one class is incompatible, exclude it from instrumentation and record that its report coverage becomes 0%; prefer report filter only if policy intentionally removes it.

Offline instrumentation: preserve original class files for report generation; instrument copies; include offline runtime; collect only after tests complete. Multiple agents or concurrent report collection can produce invalid results.

## 8. Verify+report

1. Clean test run with Kover passes.
2. Generate HTML+XML (or required formats); verify files parse and contain intended classes.
3. Seed uncovered executable branch/line; verification task must fail. Add meaningful test; task must pass.
4. Confirm filters include/exclude exact JVM class names; annotations use BINARY/RUNTIME retention where required.
5. Confirm all intended tests executed and excluded tasks did not.
6. KMP/Android report names only supported JVM/local-unit coverage; mark other targets unmeasured.
7. OUT copy `assets/integration-report.md`; exact version/engine/modules/variants/tasks/filters/rules/metrics/results/artifacts/limits.

## Fail

- docs version != latest release => inspect release changelog/source; keep coordinates consistent
- empty/0% report => verify tests ran, merger dependencies, variant, filters, original class files
- `VerifyError`/instrumentation registration failure => isolate class/agent conflict; no blanket exclusion
- threshold passes unexpectedly => inspect metric/aggregation/group/filter/variant and task path
- JaCoCo mixed across merged projects => standardize engine
- Maven integration tests required => Maven plugin currently supports `test` only; choose Gradle/agent/CLI path
