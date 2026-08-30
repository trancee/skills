# Kover multi-module/CI

## Merge graph

Select one report-generating module. Add `kover(project(...))` for every module whose production classes or tests contribute. Coverage follows declared Kover dependency graph, not every subproject automatically.

```kotlin
dependencies {
    kover(project(":core"))
    kover(project(":feature"))
    kover(project(":test-support"))
}
```
Test-scope Maven dependencies can contribute tests under Maven aggregation; Gradle uses participating project/test task wiring.

Use full task path (`:coverage:koverXmlReport`) because unqualified names can run same-named tasks across unrelated projects. Confirm task graph includes intended tests.

## CI

Recommended pipeline:
1. normal tests
2. exact merger+variant `koverVerify`
3. required HTML/XML/binary reports
4. parse/report artifact check
5. publish artifact/SARIF conversion only after producer succeeds

Cache coverage outputs only when task inputs include classes, sources, tests, engine/version, filters, and rules. Never merge binary IC reports from incompatible Kover versions/classes.

## Variants

Android variant report contains that variant classes+local unit tests. Total variant combines all. Custom variant explicitly adds named Android/JVM variants. KMP JVM report excludes JS/Native tests/code not compiled to JVM.

## Diagnose

- 0% code module: tests live in another module not connected via `kover(project)`
- missing test task: disabled instrumentation/task filter or wrong variant
- duplicate/unexpected work: invoked unqualified task in multi-project build
- report mismatch across agents: engine/version/classes/sources differ
- Android device test expectation: unsupported; use Android coverage tooling separately
