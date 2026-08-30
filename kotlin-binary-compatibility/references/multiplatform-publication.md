# Multiplatform hosts and publication inputs

## Unsupported targets

A Linux/Windows host cannot compile Apple targets. Built-in KGP validation normally preserves/infers declarations for locally unsupported targets. Setting `keepLocallyUnsupportedTargets=false` disables preservation and makes incomplete generation/check fail. Legacy KLib validation uses `strictValidation=true` for the corresponding fail-closed policy.

Choose per release policy:
- inferred/preserved: faster cross-platform development, risk of stale/inexact unsupported-target ABI
- strict: complete host required, earlier failure, less portability

Release validation should run on a host matrix that compiles every published target. Update reference dumps on a fully capable host whenever possible. Never interpret a Linux-only pass as verified Apple ABI.

Keep `rootProject.name`, module identity, target names, and publication coordinates stable; they can affect dump paths/content.

## Compilation versus publication

Compilation output can differ from the artifact consumers receive because of shading, relocation, filtering, bytecode enhancement, or custom packaging.

Built-in validator:
```kotlin
kotlin {
    @OptIn(org.jetbrains.kotlin.gradle.dsl.abi.ExperimentalAbiValidation::class)
    abiValidation {
        binariesSource.set(MAVEN_PUBLICATIONS)
    }
}
```

`MAVEN_PUBLICATIONS` requires `maven-publish`; it does not apply to Kotlin/Android or KMP projects with an Android target because those publications do not provide JARs through this path. Other enum choices are `MAIN_COMPILATION` and `NON_TEST_COMPILATIONS`.

Legacy validator can point `apiBuild.inputJar` at `jar`, `jvmJar`, or `shadowJar` archive output.

Verify artifact authority by listing final archive entries and matching transformed public classes to the dump. A task dependency alone does not prove the correct binary was inspected.
