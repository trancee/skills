# Versions and setup

## Release boundary

Inspected 2026-10-08: GitHub latest release and Cargo sparse registry agree on **Gobley 0.3.7**, commit `0309dc04fd8dbf89eb3cf9cd796c746b1979cce2`; its Cargo workspace pins **UniFFI =0.29.4**. The live bindgen table also lists 0.3.8/0.29.5, but that is not a published-release claim. Refresh release, registry, pinned manifest, and changes together before upgrading.

- [Release](https://github.com/gobley/gobley/releases/tag/v0.3.7)
- [Pinned Cargo workspace](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/Cargo.toml)
- [Cargo sparse registry](https://index.crates.io/go/bl/gobley-uniffi-bindgen)
- [Bindgen version table](https://gobley.dev/docs/bindgen#versioning)
- [Release changes](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/CHANGELOG.md)

0.3.7 repairs dependent dynamic-library loading lost in 0.3.6. 0.3.6 changes JNA mapping to direct mapping, removes `RustBufferByReference`, and uses JNA 5.18.1. Regenerate bindings and retest native dependency loading when crossing these versions; generated internals are not a stable hand-written API.

## Establish the toolchain tuple

Record Cargo/rustc, Rust toolchain pin, Gobley plugins/bindgen, resolved UniFFI, Gradle wrapper, KGP/atomicfu, daemon/compile JDK, and per-target NDK/Xcode/linker. The pinned upstream build uses Kotlin 2.1.10, AGP 8.7.3, and Gradle 8.12; this is source evidence, **not** a complete compatibility matrix or a ceiling for consumer Kotlin.

- [Pinned version catalog](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/gradle/libs.versions.toml)
- [Pinned wrapper](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/gradle/wrapper/gradle-wrapper.properties)
- [Tutorial](https://gobley.dev/docs/tutorial)
- [Development practices](https://gobley.dev/docs/common-development-practices)

Use `rust-toolchain.toml` for a project-scoped toolchain rather than changing the global Rust default. Manifest `rust-version` specifies MSRV, not an exact compiler. Rust edition 2024 requires a compatible compiler; do not mistake the bindgen documentation's historical Rust 1.72 minimum for the entire project's requirement.

```bash
cargo --version
rustc --version --verbose
rustup show active-toolchain
rustup target list --installed
java -version
./gradlew --version
```

Rustup is needed for Gobley's default automatic target installation. Custom/preinstalled toolchain -> explicitly apply `dev.gobley.rust` at the same release to expose `rust {}`; configure `rust.toolchainDirectory` and set `cargo.installTargetBeforeBuild = false` only after proving every required standard library/linker is provisioned. Cargo/UniFFI plugins alone do not expose this extension. A successful host build does not provision cross targets.

## Apply plugins at the owning module

Gobley plugins are published in Maven Central. `pluginManagement { repositories { mavenCentral(); gradlePluginPortal(); google() } }` affects plugins; dependency repositories are separate. Preserve the consumer's centralized repository policy.

```kotlin
plugins {
    kotlin("multiplatform") // version owned by consumer
    id("dev.gobley.cargo") version "0.3.7"
    id("dev.gobley.uniffi") version "0.3.7"
    kotlin("plugin.atomicfu") // same KGP version owner
}
cargo {
    packageDirectory = layout.projectDirectory.dir("rust")
}
uniffi {
    generateFromLibrary {
        packageName = "com.example.core"
    }
}
```

Cargo builds/links the crate; UniFFI generates bindings; Rust provides shared toolchain/linker/consumer configuration. Cargo alone can integrate an independently owned C ABI, but does not generate UniFFI APIs. Compose is optional.

For a new JVM proof, the bundled settings/build/Cargo/Rust/Kotlin assets form one small project. Copy the Rust asset to `src/lib.rs`, `Smoke.kt` to `src/jvmMain/kotlin/Smoke.kt`, and manifest/settings/build to project root. Use the consumer's compatible wrapper or its trusted bootstrap; the reference tuple uses Gradle 8.12/JDK 21. Run `./gradlew interopSmoke`. Existing project -> merge only the required settings; avoid a second version owner or source-set hierarchy.

The UniFFI plugin adds atomicfu, datetime, coroutines, and platform JNA dependencies by default using preferred versions. Existing constraints may win. `addDependencies=false` makes the consumer responsible for all generated imports. The Kotlin atomicfu compiler plugin remains part of the documented setup.

Sources: [Gradle plugins](https://gobley.dev/docs/gradle-plugins), [UniFFI plugin](https://gobley.dev/docs/gradle-plugins/uniffi), [pinned dependency wiring](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/build-logic/gobley-gradle-uniffi/src/main/kotlin/UniFfiPlugin.kt).

## Exercised evidence and limits

- Linux x64: published Gobley plugins/bindgen 0.3.7, UniFFI 0.29.4, Kotlin/atomicfu 2.1.10, Gradle 8.12, JDK 21, distro Rust 1.98.1. Custom host setup explicitly applied the Rust plugin, selected `/usr/bin`, and disabled automatic target installation because the host standard library was already provisioned.
- Final bundled example executed via `interopSmoke`: checked addition, integer boundary, typed overflow exception, Unicode `Greeter` call, and explicit `close()` all succeeded. Gradle built the Rust `cdylib`/`staticlib`, generated bindings, and supplied `gobley-core-linux-x86-64-debug.jar` containing `linux-x86-64/libgobley_core.so`.
- Actual CLI installation/version/help and library-mode generation succeeded. Explicit KMP TOML emitted common, JVM, Android, Native Kotlin and a C header; generation is not platform execution proof.
- Inspector CLI accepted the selected workspace member with a distinct library name; rejected ambiguous workspaces, absent manifests, missing artifact kinds/runtime dependencies, and nonexact UniFFI pins under `--strict`.
- Unverified: Android/Apple/other Native execution, minified release, 16 KB devices, external native dependencies, UDL/custom/async consumers, and separate Maven publication consumers. No compatibility claim beyond the exercised host tuple.
