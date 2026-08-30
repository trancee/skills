---
name: kotlin-gradle
description: "Configures, migrates, optimizes, and troubleshoots Kotlin Gradle builds. Use when applying the Kotlin Gradle plugin, aligning Kotlin, Gradle, JDK, or Android Gradle plugin versions, configuring compilerOptions, toolchains, dependencies, source sets, generated sources, incremental compilation, caches, build reports, daemon behavior, or Kotlin Gradle plugin variants. Don't use for Kotlin source implementation, Maven-only builds, general Gradle plugin authoring, or dedicated detekt, Dokka, Kover, Spotless, ABI-validation, and benchmarking setup."
compatibility: "Current Kotlin Gradle plugin 2.4.10 is fully supported with Gradle 7.6.3–9.5.0 and AGP 8.5.2–9.1.0. Live compatibility tables override this snapshot. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/gradle.html"
  sourceVersion: "Kotlin 2.4.10; Kotlin Help build 1155 (2026-08-26)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T14:42:58+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T14:42:58+02:00"
---

# Kotlin Gradle

## Step 1: Establish the build contract

1. DEFINE plugin setup | version alignment | compiler options | JVM toolchain | dependency/source-set change | generated sources | build performance | daemon failure | KGP variant | migration.
2. IDENTIFY affected projects, Kotlin targets/compilations/source sets, Gradle wrapper, KGP/AGP/JDK/Java target, language/API versions, repositories/catalogs/convention plugins, CI tasks, cache policy, and publication constraints.
3. READ the current [Kotlin Gradle overview](https://kotlinlang.org/docs/gradle.html), [compatibility table](https://kotlinlang.org/docs/gradle-configure-project.html), and destination-version release/migration notes before changing versions.
4. PRESERVE the repository's wrapper, Kotlin/Groovy DSL, version catalog, convention-plugin ownership, repositories, toolchain, compiler options, and dependency policy unless the request changes them.
5. ROUTE Kotlin source behavior to `kotlin-development`; route detekt, Dokka, Kover, Spotless, ABI validation, and kotlinx-benchmark configuration to their dedicated skills.

Completion: exact module/target, version tuple, configuration owner, requested build behavior, and verification task are known.

## Step 2: Inspect effective configuration

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM wrapper/KGP/AGP/JDK targets, plugin aliases, compiler-option levels, source sets, Kotlin dependencies, repositories, generated sources, cache/daemon/report properties, deprecated DSL, and warning suppressions. Then run `./gradlew projects` and `./gradlew tasks --all`; use `--info`/`--debug` only for variant/compiler-argument evidence.

Completion: static evidence and Gradle's effective projects/tasks/selected KGP variant agree.

## Step 3: Align versions and toolchains

READ `references/versions-toolchains.md` for any KGP, Gradle, AGP, JDK, `jvmTarget`, or Java compatibility change.

1. SELECT a tuple inside the live fully supported ranges; resolution outside the table is not compatibility proof.
2. KEEP one KGP version owner, normally the version catalog/root plugins block/convention build.
3. CONFIGURE one JVM toolchain policy for Kotlin and Java; set explicit targets only when they intentionally differ from toolchain inference.
4. KEEP JVM target validation fail-closed; align `compilerOptions.jvmTarget` and Java `targetCompatibility` instead of warning/ignore suppression.
5. VERIFY publication metadata reports the intended minimum JVM version.

Completion: wrapper, KGP, AGP, daemon JDK, compile toolchain, Kotlin JVM target, and Java target are compatible and intentional.

## Step 4: Configure compiler options

READ `references/compiler-options.md`.

1. MIGRATE deprecated `kotlinOptions {}`/`android.kotlinOptions` to typed `compilerOptions {}`.
2. SET broad defaults at Kotlin extension level, target differences at target level, and true one-task exceptions at compilation/task level.
3. USE typed properties (`JvmTarget`, `KotlinVersion`, `JvmDefaultMode`, JS enums) and dedicated options before `freeCompilerArgs`.
4. TRACE precedence: extension default < target override < compilation/task override.
5. RUN the exact compile task with debug logging only when applied arguments must be proven; inspect `Kotlin compiler args:` or Native `Arguments =`.

Completion: every non-default option has one owner and effective compiler arguments match intent.

## Step 5: Configure dependencies and source sets

READ `references/dependencies-source-sets.md`.

1. ADD dependencies to the narrowest owning module/source set with `api`, `implementation`, `compileOnly`, or `runtimeOnly` semantics matching consumer exposure.
2. LET KGP provide matching stdlib by default; align explicit stdlib/BOM versions with KGP policy.
3. KEEP common dependencies in shared KMP source sets and platform libraries in platform source sets.
4. ASSOCIATE custom compilations only when internal visibility/output reuse is intended.
5. REGISTER generated Kotlin through `generatedKotlin.srcDir(taskProvider)` so Gradle/IDE/task dependencies remain modeled.
6. CENTRALIZE repositories in settings when repository policy requires it; do not add a second repository/version-control seam.

Completion: dependency graph, source-set visibility, generated-source producer, and consumer metadata are correct.

## Step 6: Validate caching and daemon behavior

READ `references/caches-daemon-reports.md` for slow/non-incremental/OOM/daemon work.

1. REPRODUCE with normal incremental/cache settings before changing them.
2. USE Kotlin build reports to identify non-incremental reasons and slow phases; avoid guessing from total task duration.
3. TEST configuration cache twice and build cache through an actual clean/reuse scenario.
4. KEEP Kotlin daemon default for speed; select in-process only for measured isolation/memory needs.
5. FAIL on daemon communication when deterministic CI requires it instead of silently accepting fallback.
6. PROTECT build-report HTTP credentials/environment; never print secrets or publish verbose environment without policy.

Completion: measured evidence identifies cache/daemon behavior and the selected fix improves the reproduced path.

## Step 7: Diagnose build failures

READ `references/variants-troubleshooting.md`.

1. CLASSIFY plugin resolution | unsupported tuple | KGP variant | compiler options | JVM target | dependency variant | source set | daemon/cache | task graph.
2. RUN the narrow owning compile/task with `--stacktrace`; add `--info` only for resolution/variant evidence and `--debug` only for compiler arguments.
3. FIX the first failing configuration boundary; do not disable validation, incremental compilation, caches, or daemon fallback as a permanent symptom suppression.
4. RE-RUN the narrow task, then target/module `check` and the CI-equivalent command.

Completion: original failure is reproduced, its root configuration is corrected, and the same invocation passes.

## Step 8: Migrate or upgrade

1. SEPARATE toolchain/plugin migration from source behavior changes unless the compiler defect is the proven cause.
2. UPDATE wrapper/KGP/AGP/compiler plugins/kotlinx dependencies only as required by the chosen compatibility tuple.
3. MIGRATE removed/deprecated DSL and compiler flags to typed APIs; remove old aliases/tasks/properties in the same cutover.
4. COMPARE dependency resolution, compiler arguments, task graph, publication metadata, tests, cache reuse, and build reports before/after.
5. RECORD warnings outside full-support ranges as remaining risk, not success.

Completion: no obsolete path remains and all affected targets compile/test under the intended tuple.

## Step 9: Verify and report

1. RUN configuration/help task, narrow compile/test, module `check`, and CI-equivalent task.
2. JVM: inspect class target/publication metadata and prove related Kotlin/Java tasks agree.
3. KMP: compile every affected target; mark host-incompatible targets unverified.
4. Cache/performance: run repeat scenario and compare build reports/reuse evidence.
5. Dependency/source-set: compile producer and real consumer path; resolution alone is insufficient.
6. COPY `assets/build-report.md`; fill versions, owners, targets/options, dependencies/source sets, commands/results, cache/daemon evidence, publication metadata, and limitations.

## Error Handling

- KGP resolves outside compatibility table -> move to supported tuple or record explicit unsupported risk; never call resolution full support.
- JVM target validation fails -> align Kotlin/Java targets through one toolchain/typed target; never set ignore by default.
- Compiler option appears ineffective -> inspect lower-level target/task override and effective compiler arguments.
- Toolchain cannot download -> configure a compatible resolver/repository or verified local JDK; do not substitute Gradle daemon JDK silently.
- Kotlin daemon falls back -> inspect JVM args, memory, process reachability, and daemon logs; fail closed in deterministic CI if required.
- Build becomes non-incremental -> inspect build report reason and changed classpath/input model before disabling incremental compilation.
- Kotlin build report cannot be created -> ensure the configured report directory exists, is writable, and is not a file.
- KGP variant cannot resolve in custom configuration -> add the documented Gradle plugin API/version attributes instead of forcing an arbitrary artifact.
