# KMP migration and troubleshooting

Source: [Compatibility guide](https://kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html).

## Current migration pressure

- Android: migrate toward Google's `com.android.kotlin.multiplatform.library` and current `android` DSL per live cycle; older `androidTarget` behavior depends on KGP/AGP version
- bitcode: removed from Kotlin/Native; remove `embedBitcode`/flags
- `withJava()`: Java source sets are created by default in current KGP; remove where no Gradle Java plugin dependency requires it
- multiple similar targets: split into separate Gradle projects
- legacy KMP publications/hierarchy flags: update dependencies/plugin and use hierarchical metadata/default template
- manual `dependsOn`: removes automatic template unless explicitly reapplied

Read every compatibility-guide section crossed by the source and destination KGP versions.

## Failure map

- unresolved platform API in common: wrong source-set placement
- missing expected declaration actualization: absent/mismatched package/kind/signature or wrong hierarchy
- dependency variant missing: library does not publish target, wrong source set, legacy metadata, or forced artifact
- source directory ignored: source set not created/attached or target absent
- task absent: target/environment/compilation not declared
- target disabled: host/toolchain limitation
- duplicate/ambiguous variant: similar targets or custom attributes
- publication consumer fails: root metadata points to unpublished/incorrect target coordinate
- native link/cinterop: host/Xcode/native dependency boundary

Inspect source-set graph, target-specific dependency configurations, KGP warnings, and exact compile task. Warning-suppression properties do not repair hierarchy or host support.

Upgrade one structural concern at a time. Compare tasks, source-set graph, dependencies, tests, publications, and consumers before/after; remove obsolete flags/edges in the same cutover.
