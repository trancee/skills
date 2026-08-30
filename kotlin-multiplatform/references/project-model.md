# KMP project model

Sources: [Project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html) and [DSL reference](https://kotlinlang.org/docs/multiplatform/multiplatform-dsl-reference.html).

A target labels the source sets compiled into one platform artifact. A source set owns sources/resources, dependencies, compiler options, and a set of participating targets.

- `commonMain/commonTest`: every declared target
- leaf `<target>Main/Test`: one target
- intermediate `appleMain`, `iosMain`, `nativeMain`, etc.: target subset from hierarchy
- compilation: main/test/custom unit inside one target, collecting its default/intermediate/common source sets

Code flows downward: leaf/intermediate source sees dependencies/declarations of parents; common cannot see leaf APIs.

Declare only required targets and environments:
- JVM: `jvm()`
- JS: `js { browser() }` or `nodejs()`
- Wasm: `wasmJs`/`wasmWasi` with environment
- Native: architecture-specific targets
- Android: current Google `com.android.kotlin.multiplatform.library` path and `android` DSL where applicable

Current KMP 2.4.10 fully supports Gradle 7.6.3–9.5.0, AGP 8.5.2–9.1.0, Xcode 26.4. Live table wins.

Multiple same-platform targets in one Gradle project are discouraged/error-prone. Split implementations into projects and depend on shared API module.

Custom compilations require connection to source sets and usually `associateWith(main)` only when internal access/output dependency is deliberate. Directory creation alone does not attach code to a compilation.
