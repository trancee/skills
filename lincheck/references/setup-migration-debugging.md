# Setup, KMP placement, migration, and debugging

## Lincheck 3.7 setup

```kotlin
dependencies {
    testImplementation("org.jetbrains.lincheck:lincheck:3.7")
}
```

Use Maven Central and the repository's normal Kotlin/JVM test framework. Lincheck is JVM-only.

KMP places the dependency/tests in `jvmTest`, desktop/server JVM test, or Android host-test source set. Shared production classes may remain in `commonMain`; ordinary cross-platform tests remain in `commonTest`, but Lincheck tests execute only through a JVM target. Do not add Lincheck to `commonTest` expecting Native/JS execution.

## v2 -> v3 migration

Lincheck 3.0 changed:
- coordinates: `org.jetbrains.kotlinx:lincheck` -> `org.jetbrains.lincheck:lincheck`
- packages: `org.jetbrains.kotlinx.lincheck` -> `org.jetbrains.lincheck`
- primary scope expanded to arbitrary concurrent code through `Lincheck.runConcurrentTest`

Migrate coordinates/imports/options together. Compile every test and re-run prior failing scenarios; package changes alone do not prove semantic equivalence.

## Trace/debugging

Model checking reports a reproducible minimized scenario and execution trace. Preserve exact version, JVM, options, test, and trace. Use Lincheck IntelliJ plugin to step through supported traces. Version 3.7 improves await-loop and constructor instrumentation and Kotlin 2.4 suspend bridge handling.

Instrumentation can be affected by unsupported bytecode/native methods/reflection/agents. Minimize external frameworks and retry on the documented JVM/toolchain before excluding code. Stress failures do not include deterministic switch traces; convert the observed history into a custom/model-check scenario where possible.

Never add sleeps/logging to stabilize a trace; they perturb scheduling.
