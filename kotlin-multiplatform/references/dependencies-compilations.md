# KMP dependencies and compilations

Source: [Adding dependencies](https://kotlinlang.org/docs/multiplatform/multiplatform-add-dependencies.html).

## Dependency placement

Use base multiplatform coordinates in shared source sets. Gradle module metadata selects target variants.

- `commonMain`: library must support every project target
- intermediate source: library variant/API must support every descendant target
- leaf source: platform-only dependency
- `api`: exposed types needed by downstream source/publication
- `implementation`: internal to current source set/module

KGP adds stdlib matching plugin version automatically. `commonTest` uses `kotlin("test")`, and platform runner variants are inferred.

A platform-suffixed JVM/native artifact forced into common code bypasses variant safety and is prohibited. Query dependency insight/configurations for each failed target.

## Source-set dependencies

A child source set receives parent declarations/dependencies through hierarchy. Adding the same dependency to children is duplication unless versions/capabilities differ intentionally.

## Project dependencies

Add project dependency in the source set that consumes it. The producer must publish matching target variants. A common project dependency requires compatible variants for all consumer targets.

## Compilations

Each non-Android target has main/test compilations; Android compilation model differs. A custom compilation's default source set is not automatically connected to main. `associateWith(main)` adds main outputs and internal visibility. Use for integration tests/benchmarks only with explicit semantic need.

Compiler options can live extension/target/compilation level. Keep shared defaults high and platform differences low. Use `kotlin-gradle` for option/toolchain troubleshooting.
