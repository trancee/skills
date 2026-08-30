# Hierarchy and expect/actual

Sources: [Hierarchy](https://kotlinlang.org/docs/multiplatform/multiplatform-hierarchy.html) and [expect/actual](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html).

## Default hierarchy

KGP creates intermediate source sets only when matching targets exist. Prefer generated static accessors (`appleMain`, `iosMain`, `nativeMain`). Manual `dependsOn` edges disable automatic template application unless `applyDefaultHierarchyTemplate()` is called explicitly.

Use manual hierarchy only for a sharing set absent from the template. If opting out with `kotlin.mpp.applyDefaultHierarchyTemplate=false`, define every needed main/test edge consistently. Standard source-set names must retain ecosystem meaning.

Unsupported shared groups include several JVM targets, JVM+Android, and several JS targets. Split modules instead of inventing ambiguous hierarchies.

## Expect/actual

Rules:
- expect in common/intermediate, no implementation
- actual in every target path, same package/kind/name/compatible signature
- intermediate actual serves all descendant targets
- compiler merges expect+actual per target

Prefer:
1. common interface and dependency injection
2. expect factory/function/property returning common interface
3. expected object/annotation/enum when semantics require
4. expected class only with Beta acceptance and `-Xexpect-actual-classes`

Interfaces allow multiple implementations and test fakes without binding common API to platform class shapes.

Verify via source-set-specific compile for every target. IDE gutter navigation helps but is not build proof. Public expect/actual changes affect every platform API and binary publication.
