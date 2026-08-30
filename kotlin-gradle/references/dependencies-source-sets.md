# Dependencies, source sets, and generated code

Source: [configure a Gradle project](https://kotlinlang.org/docs/gradle-configure-project.html).

## Dependency semantics

- `api`: dependency types appear in published consumer API
- `implementation`: internal compile/runtime dependency
- `compileOnly`: compile API supplied elsewhere at runtime
- `runtimeOnly`: runtime implementation absent from compile API

KGP adds a platform-appropriate stdlib matching KGP to each source set. An explicit stdlib suppresses the automatic one; verify intentional version alignment. Prefer the Kotlin BOM only when repository policy needs explicit alignment.

KMP: add shared libraries to `commonMain`/shared source sets using base artifact names; add platform-only libraries to the platform source set. Top-level common dependencies are experimental in current KGP and require explicit opt-in. `commonTest` with `kotlin("test")` allows platform framework inference.

## Source sets and compilations

Keep Kotlin and Java in conventional separate directories unless existing layout requires overrides. Custom compilation `associateWith(main)` grants internal visibility and output reuse; use it only for deliberate test/benchmark/integration boundaries.

Dependencies flow through source-set/compilation hierarchy, not directory names alone. Compile a real consumer source set to verify visibility and variant selection.

## Generated sources

Model the producer output:
```kotlin
val generator = tasks.register("generateKotlin") {
    val output = layout.buildDirectory.dir("generated/kotlin")
    outputs.dir(output)
    // task action writes files
}

kotlin.sourceSets.getByName("main").generatedKotlin.srcDir(generator)
```

Use task providers/directories so Gradle and IDE infer dependency and generated status. Avoid writing generated files under checked-in source roots.

## Repositories

Centralize repositories through `dependencyResolutionManagement` when the project uses it. Subproject repositories can override central policy depending on repositories mode. Preserve credentials/content filters/exclusive repositories; never duplicate repository declarations to fix a coordinate typo.
