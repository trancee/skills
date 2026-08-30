# Kotlin Gradle troubleshooting

## Diagnose in order

1. wrapper starts and settings/build scripts compile
2. plugin repositories and plugin alias/version resolve
3. KGP/Gradle/AGP/JDK tuple is fully supported
4. selected KGP variant matches Gradle
5. project/source-set dependency variant resolves
6. compiler options/toolchain/Java target agree
7. Kotlin daemon starts without fallback/OOM
8. compile/test/link/package task runs

Use `--stacktrace` for failure cause, `--info` for dependency/KGP variant selection, and `--debug` only for effective compiler arguments. Redact secrets from logs.

## Frequent failures

- `Inconsistent JVM-target compatibility`: align toolchain, `JvmTarget`, and Java target; preserve error validation
- no matching KGP variant: compare wrapper with live compatibility table; custom configurations need Gradle plugin API/JVM attributes
- plugin not found: verify `pluginManagement` repositories and alias; Maven Central alone does not replace Plugin Portal when marker is absent
- dependency no matching variant: verify target/source set, Kotlin metadata compatibility, attributes, and repository; do not force a JVM artifact into common code
- generated symbol missing: register producer through `generatedKotlin.srcDir(taskProvider)` and inspect task dependency
- circular friend/artifact dependency: inspect compilation associations; `kotlin.build.archivesTaskOutputAsFriendModule=false` is a documented narrow escape, not a default
- compiler option ignored: lower-level task override wins; inspect compiler args
- daemon connection fallback: stop stale Gradle daemons, inspect memory/JDK/args, reproduce with fallback disabled
- cache miss/non-incremental: read Kotlin build report reason; compare task inputs/classpath snapshots before configuration changes

## Upgrade evidence

Capture before/after: wrapper/KGP variant, dependency graph, compiler args, class target/publication metadata, task graph, tests, configuration-cache reuse, clean build-cache reuse, and Kotlin build reports. An upgrade that only compiles one host target remains unverified for other KMP targets.
