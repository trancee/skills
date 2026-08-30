# KMP and Android configurations

Source: [KSP with Kotlin Multiplatform](https://kotlinlang.org/docs/ksp-multiplatform.html) and the [configuration reference](https://github.com/google/ksp#ksp-gradle-configurations-reference).

Single-platform:
- `ksp`: main
- `kspTest`: unit test
- `ksp<SourceSet>`: custom JVM source set
- Android `ksp<BuildType>`, `ksp<Flavor>`, `ksp<Flavor><BuildType>`, `kspTest<Variant>`, `kspAndroidTest<Variant>` as exposed by the actual plugin/variant model

KMP:
- target main: `ksp<Target>` (`jvm` -> `kspJvm`, not `kspJvmMain`)
- target test: `ksp<Target>Test`
- Android KMP: derive host/device configurations from source-set names (`kspAndroidHostTest`, `kspAndroidDeviceTest`, etc.)
- common metadata: `kspCommonMainMetadata` only for deliberate common processing

Use `./gradlew :module:dependencies` and task listing to discover exact names; custom target names change the suffix. A KSP task exists only where a processor dependency is configured.

Global `ksp` in KMP is deprecated/blocked. `ksp.allow.all.target.configuration=true` merely permits legacy behavior with warning and should not survive migration.

The processor artifact runs on the build JVM, but receives platform info and generates code for the target compilation. Keep generated common code portable; test JS/Native/Wasm/Android models and platform-specific type mapping separately.

Host/native cross-compilation behavior follows Kotlin Native support (`kotlin.native.enableKlibsCrossCompilation`). Record tasks disabled by host and run them on capable CI rather than treating absence as success.
