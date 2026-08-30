# Testing and migration

Sources: [quickstart](https://kotlinlang.org/docs/ksp-quickstart.html), [kapt migration](https://kotlinlang.org/docs/ksp-kapt-migration.html), [FAQ](https://kotlinlang.org/docs/ksp-faq.html), and [KSP 2.3.11 release](https://github.com/google/ksp/releases/tag/2.3.11).

## Processor test pyramid

1. pure model/name/type-render helpers with exhaustive edge cases
2. KSP2 processor invocation/integration fixture containing annotation + processor/provider service + consumer
3. compile generated Kotlin/Java and execute representative consumer
4. diagnostic tests for malformed/unsupported/error/deferred symbols
5. multi-processor/multi-round generated dependency
6. incremental add/change/remove/rename/option/classpath matrix versus clean output
7. KMP/Android target/variant tasks and packaged processor JAR service entry

Assert generated API/behavior and diagnostics, not implementation visitation order. Text snapshots help review but compilation is required.

## kapt migration

Inventory each `kapt`/`annotationProcessor` dependency and confirm that exact library/version supports KSP. Migrate one processor family at a time:
- apply KSP2 plugin
- move only supported processor dependency to exact `ksp*` configuration
- preserve required runtime/annotation dependencies and processor options
- compare generated API/diagnostics/runtime behavior and clean/incremental builds
- migrate all changed generated callers
- remove that processor's kapt configuration; retain kapt only for other unsupported processors

A Java annotation processor is not automatically a KSP processor.

## KSP1 migration

KSP 2.3.0 decoupled versioning from Kotlin and stopped being a compiler plugin; current KSP has removed KSP1. Replace old `<kotlin>-<ksp>` versions, remove `ksp.useKSP2` toggles/compiler-daemon debug paths, verify KSP2 API behavior differences/error types, and move heap/debug configuration to Gradle daemon.
