---
name: gobley
description: "Integrates Rust libraries into Kotlin Multiplatform with Gobley. Use when configuring dev.gobley.cargo or dev.gobley.uniffi, generating UniFFI Kotlin bindings, packaging native libraries for Android/JVM/Kotlin Native, mapping custom types, or diagnosing Rust cross-compilation and FFI lifetime failures. Don't use for standalone Rust development, UniFFI Swift/Python bindings, Kotlin-to-Swift interop, or unsupported JS/Wasm targets."
compatibility: "Baseline: Gobley 0.3.7 with UniFFI 0.29.4. Requires Cargo/Rust, a compatible Kotlin/Gradle/JDK tuple, Android SDK/NDK for Android, and macOS/Xcode for Apple builds. Inspector requires Python 3.11+. JS/Wasm UniFFI implementations are stubs, not working Rust interop."
metadata:
  category: "development"
  source: "https://github.com/gobley/gobley"
  sourceVersion: "Gobley v0.3.7@0309dc04fd8dbf89eb3cf9cd796c746b1979cce2; UniFFI 0.29.4; documentation checked 2026-10-08"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-08T13:13:46+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-08T13:13:46+02:00"
---

# Gobley

## Step 1: Establish the interop contract

1. Record owning Gradle module and Cargo package/workspace, Rust library crate name, Kotlin package, API boundary, target architectures, host matrix, debug/release policy, and publication consumers.
2. Read `references/versions-setup.md` before installation/upgrades. Confirm the latest published release and its exact UniFFI dependency; documentation can describe unpublished versions.
3. Preserve existing Kotlin/Gradle/AGP versions, catalogs, module boundaries, and target names. Route general build alignment to `kotlin-gradle`, source-set design to `kotlin-multiplatform`, and Kotlin/Swift framework export to `kotlin-native-apple-interop`.
4. Limit working UniFFI targets to Android, JVM, and Kotlin/Native. JS/Wasm generated stubs throw `NotImplementedError`; Cargo WASM embedding alone does not implement UniFFI bindings.

Gate: one explicit module/crate/API contract and executable target/host matrix.

## Step 2: Locate and validate the Rust library

1. Resolve this package's `scripts/` locally; pass the consumer's manifest explicitly:
   ```bash
   python3 scripts/inspect-cargo.py --manifest path/to/Cargo.toml --require-kind cdylib --require-kind staticlib --uniffi-version 0.29.4 --json
   ```
2. For a virtual workspace, select the intended member with `--package NAME`. Use Cargo's reported library target name, not the package name with guessed punctuation.
3. Require `cdylib` for Android/JVM packaging and `staticlib` for Kotlin/Native; request only the kinds needed by the selected targets. Pin the actual resolved UniFFI version in the lockfile as well as the manifest.
4. New crate only: copy `assets/Cargo.toml` and `assets/lib.rs` into the owning module; adapt names and API. Existing crate: preserve its sources/features and add only missing interop configuration.
5. Proc macros -> add `uniffi::setup_scaffolding!()` once at crate root and export the intended API. Existing UDL -> retain its build-script scaffolding instead; read `references/bindings-api.md`.

Gate: Cargo metadata identifies the correct library, artifact kinds, source entry point, and UniFFI pin; Rust compiles.

## Step 3: Connect Gradle and generate bindings

1. Read `references/versions-setup.md` and `references/gradle-packaging.md`.
2. Add Maven Central to **plugin management** as well as dependency resolution. Apply matched `dev.gobley.cargo` and `dev.gobley.uniffi` releases plus the Kotlin atomicfu compiler plugin aligned with KGP.
3. For a new host-JVM proof, copy `assets/settings.gradle.kts` and `assets/build.gradle.kts`, then place `assets/Smoke.kt` at `src/jvmMain/kotlin/Smoke.kt`. Run `./gradlew interopSmoke` with a compatible wrapper. Their pinned tuple is an example, not an instruction to downgrade an existing project.
4. Set `cargo.packageDirectory` if Cargo is outside the Gradle module directory. Select **one** `generateFromLibrary` or `generateFromUdl` configuration; bindgen uses library mode by default.
5. Let Gobley own generated source directories, dependencies, and cinterop/link tasks. Edit Rust/UDL/configuration, not generated Kotlin. Inspect selected dependency versions if the consumer already constrains them.
6. Run the consumer wrapper's `tasks --all`; discover Cargo and UniFFI tasks for that module, then run its narrow compile task. IDE sync may execute Rust builds and binding generation.

Gate: regenerated bindings compile in each affected source set and match the linked Rust binary.

## Step 4: Implement the exposed API safely

1. Read `references/bindings-api.md` for records, errors, objects, custom/external types, serialization, or async functions.
2. Keep business logic in Rust and expose coarse-grained operations; UniFFI serializes values across the boundary, so avoid repeated large-data round trips.
3. Map expected failures to exported typed errors. Keep panic behavior separate from the public error contract.
4. Give each generated Rust object an explicit owner; call `close()` when ownership ends, including exceptional paths. Closing a Kotlin proxy releases its Rust reference, not necessarily the final `Arc`.
5. Keep binding/runtime checksum checks enabled. Resolve mismatches by rebuilding the same crate/version/features, not by setting `omitChecksums`.

Gate: real calls prove results, typed failures, ownership, and any configured type conversions/cancellation.

## Step 5: Build, package, and publish selected targets

1. Read `references/gradle-packaging.md`; cross-compilation/link/runtime failure -> also read `references/platform-troubleshooting.md`.
2. Android -> set intended NDK/ABIs; inspect packaged Rust and dependent `.so` files, generated JNA keep rules, and 16 KB compatibility. Exercise a minified release on an appropriate device/emulator.
3. JVM -> choose shipped Rust targets using `embedRustLibrary`; host-only filtering is for local proof, not a multi-platform release. Verify runtime JAR classifiers and the actual JVM process architecture.
4. Kotlin/Native -> verify static linking/cinterop on capable hosts; keep device/simulator architectures distinct and align Rust, C/C++, Kotlin framework, and app deployment floors.
5. Multi-module consumer -> apply `dev.gobley.rust` where consuming Gobley modules, including Android local-unit-test consumers.
6. Publication -> explicitly select `jvmPublishingVariant` and `nativeVariant`; publish/resolve native runtime artifacts as well as Kotlin metadata/classes. Validate a separate consumer outside the producer build.

Gate: every claimed target executes Rust through its packaged artifact; publication consumers resolve the intended release binaries.

## Step 6: Verify and report

1. Run Cargo checks/tests for Rust behavior and target-specific Kotlin compile/test tasks for the interop contract. A generated file, passing IDE sync, or Kotlin compilation alone does not prove native loading.
2. Exercise a real generated call plus a typed error and object lifecycle; for async/custom types, also exercise cancellation or round-trip boundaries. Rebuild after Rust API changes.
3. Inspect final APK/AAR/JAR/framework artifacts and dependent native libraries; test release variants separately from debug.
4. Copy `assets/interop-report.md`; record version tuple, crate/config ownership, targets, task commands, results, packaging, consumers, and unverified hosts. Keep credentials and private source paths out of shared reports.
5. Host unavailable -> finish reachable checks and mark those targets unverified; do not replace required implementations with stubs.

## Error Handling

- Plugin not found -> confirm Gobley release coordinates and `pluginManagement.repositories.mavenCentral()`.
- Crate not found in library -> check selected crate/binary, scaffolding, export metadata, generation mode, and exact UniFFI version.
- JS/Wasm calls fail -> generated stubs are unsupported interop; use a separately implemented supported boundary or remove that claim.
- Native library fails to load -> distinguish missing classifier/ABI/dependent library from missing exports/JNA keep rules; inspect the actual packaged artifact.
- Host-only unit tests fail -> include the host JVM runtime and apply the Rust plugin in consumer modules; Android `.so` files do not run in the desktop JVM.
- Linker/deployment/page-size error -> use `references/platform-troubleshooting.md`; fix the toolchain/artifact boundary instead of suppressing diagnostics.
- Cargo inspector fails -> follow its stderr correction; metadata evidence does not validate Gradle configuration or installed binaries.
