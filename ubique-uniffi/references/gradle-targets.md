# Gradle targets, packaging, and migration

Use the version contract in `versions-generation.md` through the core procedure. This reference covers the released 1.3.1 unified plugin, not Gobley's separate plugin/variant/classifier DSL.

## Module configuration

Apply `kotlin("multiplatform")` and `ch.ubique.uniffi.plugin` in the owning module. Provide Maven Central in plugin management and dependency resolution. Set `cargo.packageDirectory` to the directory containing Cargo.toml when it differs from the module root.

Choose one generation mode:

```kotlin
uniffi {
    generateFromLibrary {
        packageName = "example.core"
    }
}
```

Library mode builds a host library and extracts its UniFFI metadata; it works with proc macros and UDL scaffolding. Pure UDL mode can instead use `generateFromUdl { udlFile = layout.projectDirectory.file("src/core.udl") }`, without building the host library for generation. Keep the Rust build-script/include scaffolding and use library mode for metadata spanning proc macros or multiple crates.

`packageName` overrides root TOML `package_name` for the selected crate since 1.3.0. Replace the old, ineffective `namespace` setting; do not combine conflicting package owners. The plugin adds the matching shared runtime and generated-code dependencies unless explicitly disabled.

Sources: [getting started](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/getting-started/), [generation modes](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/proc-macros-vs-udl/), [Gradle DSL](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/configuration/gradle-dsl/).

## Target matrix and release scope

| Kotlin target | Rust target / selection | Artifact delivery |
| --- | --- | --- |
| `jvm()` | host in debug; desktop matrix in release | dynamic library in JVM resources, JNA |
| `android { }` | selected debug ABIs; three supported release ABIs | dynamic library in AGP jniLibs, JNA |
| `iosArm64()` | `aarch64-apple-ios` | static library/cinterop |
| `iosSimulatorArm64()` | `aarch64-apple-ios-sim` | static library/cinterop |
| `iosX64()` | `x86_64-apple-ios` | static library/cinterop |
| `macosArm64()` | `aarch64-apple-darwin` | static library/cinterop |
| `linuxX64()` / `linuxArm64()` | corresponding Linux GNU triple | static library/cinterop |
| `mingwX64()` | `x86_64-pc-windows-gnu` | static library/cinterop |

Unsupported targets fail with `Unhandled target`; no JS/Wasm stubs are promised. Native `macosX64` was removed in 1.1.0, while Intel macOS JVM libraries remain part of the release matrix. Apple builds require a capable macOS/Xcode host; guard target declarations using `ch.ubique.uniffi.plugin.model.RustHost.Platform.MacOS.isCurrent` when the script also runs elsewhere.

Default builds use Cargo dev profile. `-PreleaseBuild=true` enables optimized Cargo builds **and expands target selection**: JVM includes arm64/x64 macOS and Linux plus x64 Windows; Android includes arm64-v8a, armeabi-v7a, and x86_64. A debug JVM artifact is host-specific, not restricted to the literal machine that built it. Release JVM builds require all selected cross C toolchains/linkers.

JVM binaries are copied into resources under JNA platform prefixes, e.g. `linux-x86-64/libcore.so`. Verify both the crate library and the shared runtime's native library on the runtime classpath. Do not import Gobley's separate runtime-JAR classifier recipe or `embedRustLibrary` controls. The diagnostic `uniffi.component.<namespace>.libraryOverride` must not hide an incomplete published artifact.

Sources: [targets](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/targets/), [pinned target mapping](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/build-logic/gradle-plugin/src/main/kotlin/ch/ubique/uniffi/plugin/model/BuildTarget.kt).

## Android and host tests

Since 1.1.0, use AGP 9's Android-KMP library plugin, not `com.android.library` / `androidTarget()`:

```kotlin
plugins {
    kotlin("multiplatform") // consumer version owner
    id("com.android.kotlin.multiplatform.library") version "9.3.1"
    id("ch.ubique.uniffi.plugin") version "1.3.1"
}
kotlin {
    android {
        namespace = "example.core"
        compileSdk = 37
        minSdk = 21
        withHostTest {}
    }
}
cargo {
    ndkVersion = "28.1.13356709"
    androidDebugAbis.add("arm64-v8a")
}
```

The released runtime is built with compileSdk 37 and minSdk 21. Validate the consumer's resolved AAR metadata and SDK policy; the NDK version above is an example pin. NDK selection is explicit pin, otherwise newest under ANDROID_HOME/ndk, falling back to ANDROID_NDK_ROOT. Debug ABI precedence is DSL selection, then `-PandroidAbis=...`, then host defaults; supported values are arm64-v8a, armeabi-v7a, and x86_64. This does not narrow release ABIs.

Host tests execute a desktop JVM, so the plugin builds/copies a host library when `withHostTest {}` is enabled. They are not device/ABI proof. The shared runtime ships consumer R8 rules for JNA/generated structures; inspect the final minified app and every native dependency, including applicable 16 KB ELF/ZIP alignment, using [Android's guide](https://developer.android.com/guide/practices/page-sizes).

## Native commonization and linker failures

Set `kotlin.mpp.enableCInteropCommonization=true` in gradle.properties for any Native target. Generated code lives in shared nativeMain; the plugin creates `uniffi-cinterop` and target .def files. Keep runtime/crate `common.h` identities aligned rather than manually copying or renaming shared FFI types.

1.3.0 fixes duplicated Native RustBuffer identity (`IrClassSymbolImpl is already bound`) and moves primitive converters/cleaner into the runtime. 1.3.1 feeds a repository-provided runtime cinterop KLIB into shared-source commonization, fixing unresolved FFI references in `compileNativeMainKotlinMetadata`. These are header/runtime identity problems, **not** old-LLVM linker problems.

For actual unknown-relocation/object-format failures from a proven Kotlin/Native/Rust LLVM mismatch:

```kotlin
import ch.ubique.uniffi.plugin.extensions.useRustUpLinker
kotlin {
    mingwX64 {
        compilations.getByName("test") { useRustUpLinker() }
    }
}
```

The helper requires the active Rustup toolchain's linker. It does not replace missing Apple SDKs or fix a wrong deployment minimum. Align Rust, dependent C/C++ objects, Kotlin framework, and app deployment floors; keep device/simulator architectures distinct.

Sources: [1.3.1 release](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/releases/tag/v1.3.1), [shared headers](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/internals/bindgen/#headers), [linker helper](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/build-logic/gradle-plugin/src/main/kotlin/ch/ubique/uniffi/plugin/extensions/RustExtension.kt).

## Build reuse and diagnostics

Discover actual module tasks with `tasks --all`. Kotlin compile tasks depend on binding/native producers; task families include installBindgen, buildBindings, buildLibraryForBindings, cargoBuild<RustTarget><Debug|Release>, mergeUniffiJvmResources, mergeUniffiAndroidJniLibs, and mergeUniffiAndroidHostTestResources. IDE sync also generates bindings, but uses dummy Native cinterop definitions rather than pretending cross-target binaries were verified.

`cargo.targetDirectory` or CARGO_TARGET_DIR can share Cargo artifacts across Gradle builds; keep Gradle output directories separate. The Cargo directory survives Gradle clean. Configure `rustcWrapper`/`rustcWorkspaceWrapper` for an existing sccache policy, or `compilations.linuxX64 { useCross = true }` for a provisioned cross environment. Configuration-time metadata is no-deps; bindgen's full type resolution has different requirements.

For stale binaries, correct the input/source/runtime mismatch, then clean only owned outputs. Do not wipe global caches or disable checksum checks. `formatCode=true` invokes external ktlint; unresolved formatting warnings are not a successful lint gate.

## Migration and failure routing

- Legacy Trixnity -> v0.7.0 was the last legacy-style branch; current Ubique uses one rewritten plugin. Do not infer chronology from old version numbers; remove obsolete plugin IDs and migrate their callers/configuration together.
- Ubique 1.0.x -> migrate Android plugin/source sets to AGP 9, remove unsupported Native macosX64, and replace injected datetime assumptions with the current Kotlin time APIs.
- 1.1.x -> 1.2.0 changes UniFFI from 0.28 to 0.32, including NoPointer -> NoHandle, borrowed-byte support, and callback vtable changes. Regenerate and rebuild every participating module.
- 1.3.x -> use packageName, remove ignored import_pointer_from/disable_java_cleaner settings, and use the matching tagged generator/runtime. For older generators configured from a moving branch, explicitly pin a supported tag or revision.
- Missing target/NDK -> provision the real standard library/compiler/linker; the plugin retries a missing Rust target with Rustup, but Rustup target installation does not install cross C linkers.
- Load failure -> check platform resources, native transitive dependencies, process architecture, and debug/release matrix before using overrides.
- spmForKmp conflict -> use supported spmForKmp >=1.9.5 or inspect the exact legacy workaround; route general Swift integration to its owner rather than changing Ubique's cinterop identity blindly.

Sources: [pinned changelog](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/CHANGELOG.md), [troubleshooting](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/troubleshooting/), [build performance](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/configuration/build-performance/).
