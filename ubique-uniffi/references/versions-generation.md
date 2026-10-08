# Release pins, setup, and manual generation

## Establish the actual release

Verified 2026-10-08: GitHub latest release, Maven runtime metadata, and plugin marker publish **1.3.1**, commit `b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300`. README/site examples still use 1.3.0. Use 1.3.1 for this baseline; do not infer an unreleased version from moving prose.

- [Release notes](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/releases/tag/v1.3.1)
- [Pinned Rust workspace](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/Cargo.toml)
- [Published runtime metadata](https://repo.maven.apache.org/maven2/ch/ubique/uniffi/runtime/maven-metadata.xml)
- [Published plugin marker](https://repo.maven.apache.org/maven2/ch/ubique/uniffi/plugin/ch.ubique.uniffi.plugin.gradle.plugin/1.3.1/ch.ubique.uniffi.plugin.gradle.plugin-1.3.1.pom)

Pin these as separate identities:

| Component | Baseline | Ownership |
| --- | --- | --- |
| Gradle plugin | `ch.ubique.uniffi.plugin:1.3.1` | version catalog/root/convention plugin |
| Kotlin shared runtime | `ch.ubique.uniffi:runtime:1.3.1` | automatically added, unless explicitly disabled |
| Binding generator | same 1.3.1 tag/revision | plugin's default pinned Git source |
| Mozilla UniFFI | exactly `0.32.0` | Cargo manifest + resolved lockfile |

The generator crate is named `uniffi_bindgen_kotlin_multiplatform`; its executable is `uniffi-bindgen-kotlin-multiplatform`. Its manifest version is **0.0.0**, so CLI `--version` is not a release identity. Record Git revision/source, installation output, and binary checksum instead of treating `0.0.0` as the supported UniFFI version.

1.3.1 fixes commonization of a repository-provided runtime cinterop for `compileNativeMainKotlinMetadata`. The tag's CHANGELOG still labels that fix Unreleased; the release notes and code establish inclusion. 1.3.0 fixes shared Native header identity, uses runtime primitive converters/cleaner on Native, exposes `packageName`, and pins the default generator tag. The deprecated `namespace` setting, `import_pointer_from`, and `disable_java_cleaner` are not current configuration.

Sources: [pinned changelog](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/CHANGELOG.md), [pinned bindgen manifest](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/bindgen/Cargo.toml).

## Provision a compatible consumer

Documentation floors: Rust 1.91+, UniFFI 0.32.0 exactly, Gradle 9.6.1+, Kotlin 2.4.0+, JDK 17+, and AGP 9 only for Android. The pinned upstream tuple is Rust 1.97.1, Gradle 9.7.0, Kotlin 2.4.0, AGP 9.3.1. The plugin artifact targets JVM 17; its upstream daemon pin to JDK 25 is not a consumer JDK-25 requirement.

Use Rustup for supported target/toolchain management, Maven Central in plugin and dependency repositories, Android SDK/NDK for Android, and capable native hosts/linkers. A preinstalled host Rust toolchain can build that host; it does not provide missing cross-target standard libraries or Rustup's linker helper.

```bash
cargo --version
rustc --version --verbose
rustup show active-toolchain
rustup target list --installed
java -version
./gradlew --version
```

Use project-scoped toolchain/version ownership; preserve the consumer's catalogs/wrapper rather than blindly copying upstream versions. The bundled JVM example uses Kotlin 2.4.0, plugin 1.3.1, and JDK 21. Copy Cargo/settings/build to project root, Rust to `src/lib.rs`, and Kotlin smoke to `src/jvmMain/kotlin/Smoke.kt`. Run the consumer's compatible wrapper with `interopSmoke`; bootstrap a trusted wrapper only through the repository's normal process.

Keep the unified plugin's automatic runtime and dependency insertion for the initial proof. It adds Okio 3.18.1, atomicfu 0.33.0, coroutines 1.11.0, and platform JNA 5.19.1. Do not copy Gobley's atomicfu compiler-plugin requirement into this consumer setup. Inspect the effective graph when overriding dependencies.

Sources: [requirements](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/requirements/), [getting started](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/getting-started/), [published plugin JVM metadata](https://repo.maven.apache.org/maven2/ch/ubique/uniffi/plugin/1.3.1/plugin-1.3.1.module), [dependency ownership](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/configuration/dependencies/).

## Manual generator branch

Prefer Gradle's `installBindgen` and `buildBindings`, which provide runtime dependencies, target registration, and native packaging. A separate build system must own those responsibilities explicitly.

Install the exact supported source, not a similarly named registry package or the legacy Trixnity generator:

```bash
cargo install --git https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings.git \
  --rev b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300 --locked \
  --bin uniffi-bindgen-kotlin-multiplatform uniffi_bindgen_kotlin_multiplatform
uniffi-bindgen-kotlin-multiplatform --help
```

Library mode: run from the owning Cargo package/workspace because the CLI executes `cargo metadata` in its working directory.

```bash
uniffi-bindgen-kotlin-multiplatform --library path/to/libubique_core.so \
  --crate ubique_core --package-name example.ubique --out-dir build/bindings
```

`--out-dir` is required with `--library`; the library is the positional source. Do not combine `--lib-file` with `--library`. UDL mode takes a UDL positional source and optional `--lib-file`; preserve its Rust build-script/include scaffolding. `generateFromLibrary()` can also extract UDL metadata from a built crate.

Root TOML options live next to Cargo.toml, **not** under stock UniFFI's `[bindings.kotlin]`. `--package-name` overrides only the selected crate's package; other crates use their own TOML/package map. Keep one package owner.

```toml
package_name = "example.ubique"
generate_immutable_records = true
```

Normal generator output includes common/JVM/Android/Native Kotlin and `nativeInterop/cinterop/headers/<namespace>/...` plus shared `nativeInterop/cinterop/headers/common/common.h`. It imports `uniffi.runtime.*`; copying generated Kotlin without the matching runtime is incomplete integration. The generator's `runtime` Cargo feature is for building the shared runtime itself, not ordinary consumer bindings.

`--metadata-no-deps` suppresses dependency graph resolution and can lose external types outside the workspace; use only after proving all needed type/package metadata remains available. Library filenames, Cargo package/library names, UniFFI namespaces, and Kotlin packages are distinct; inspect Cargo metadata instead of guessing.

Sources: [pinned CLI](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/blob/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/bindgen/src/main.rs), [bindgen architecture](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/internals/bindgen/), [TOML options](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/configuration/uniffi-toml/).
