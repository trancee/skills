---
name: ubique-uniffi
description: "Integrates Rust with Kotlin Multiplatform using Ubique's UniFFI bindings. Use when configuring ch.ubique.uniffi.plugin and ch.ubique.uniffi:runtime, generating bindings with uniffi-bindgen-kotlin-multiplatform, sharing Rust objects across modules, selecting Android/JVM/Native builds, or migrating Ubique and legacy Trixnity integrations. Don't use for Gobley plugins, stock UniFFI Swift/Python generators, Kotlin-to-Swift framework export, or JS/Wasm interop."
compatibility: "Baseline: Ubique plugin/runtime/bindgen 1.3.1 with UniFFI exactly 0.32.0; Rust >=1.91, Gradle >=9.6.1, Kotlin >=2.4.0, JDK >=17. Android requires AGP 9 Android-KMP plugin and NDK; Apple execution requires macOS/Xcode. Native requires cinterop commonization. Lockfile helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings"
  sourceVersion: "v1.3.1@b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300; UniFFI 0.32.0; repository and documentation inspected 2026-10-08"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-08T13:30:08+02:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-08T13:57:46+02:00"
---

# Ubique UniFFI Kotlin Multiplatform

## Step 1: Select the fork and version contract

1. Record owning Gradle modules, Cargo packages/workspace, Rust library names, Kotlin packages, shared types, target/host matrix, release/publication scope, and installed toolchain tuple.
2. Read `references/versions-generation.md`. Pin the **Ubique** plugin, shared runtime, and generator together; pin UniFFI separately to the exact supported version. Latest source/docs can differ from published releases.
3. Route Gobley `dev.gobley.*` integration to `gobley`; preserve a single fork per integration. Route general toolchain/hierarchy work to `kotlin-gradle` / `kotlin-multiplatform` and framework-to-Swift export to `kotlin-native-apple-interop`.
4. Treat unsupported Kotlin targets as configuration failures, not working stubs. Specify only shipped targets on capable hosts.

Gate: fork, module/crate ownership, exact version tuple, and executable target matrix are explicit.

## Step 2: Establish runtime and Rust safety invariants

1. Read `references/runtime-api.md` before sharing objects, buffers, callbacks, or types across modules.
2. Require Rust's default allocator in every participating crate and dependency. A custom `#[global_allocator]` can corrupt memory because runtime-allocated buffers are freed by a receiving crate. Audit dependency sources/features; a lockfile does not prove allocator compatibility.
3. Resolve Cargo dependencies and check each relevant lockfile from this skill package:
   ```bash
   python3 scripts/check-uniffi-lock.py --lock path/to/Cargo.lock --expected 0.32.0 --json
   ```
4. Repeat `--lock` for independent workspaces. Treat helper output as resolved-version evidence only; also verify actual loaded binaries, plugin/runtime/generator revision, and shared-crate versions.
5. New crate -> copy `assets/Cargo.toml` and `assets/lib.rs` to the owning module, placing Rust at `src/lib.rs`. Use `lib` for Rust dependents, `cdylib` for JVM/Android, and `staticlib` for Native. Existing crate -> preserve feature/source ownership.

Gate: version graph and default-allocator/shared-crate invariants hold before crossing the FFI.

## Step 3: Configure and generate one module

1. Read `references/gradle-targets.md`.
2. Apply KMP plus the unified `ch.ubique.uniffi.plugin`; configure Maven Central for plugin and dependency resolution. Do not add Gobley's separate Cargo/Rust/UniFFI plugins or compiler-plugin assumptions.
3. Set `cargo.packageDirectory` only when the manifest is outside the Gradle module. Select one `generateFromLibrary()` or `generateFromUdl { udlFile = ... }`; neither is implicit.
4. Proc macros -> export the API and call `uniffi::setup_scaffolding!()` once. UDL -> retain generated/include scaffolding; do not add a second setup macro to the same crate.
5. Set package ownership with `packageName` in the generation block or root-level `package_name` in `uniffi.toml`; Gradle takes precedence in 1.3.x.
6. Keep automatic runtime/dependencies unless all replacements are explicitly owned. Runtime version must match the generator/plugin across modules.
7. Any Native target -> set `kotlin.mpp.enableCInteropCommonization=true`. Use the 1.3.1 published-runtime commonizer fix rather than cloning the runtime into the app or suppressing Native diagnostics.
8. New host-JVM proof -> copy settings/build assets and `assets/Smoke.kt` to `src/jvmMain/kotlin/Smoke.kt`; run `./gradlew interopSmoke` using a compatible wrapper. Existing project -> merge required configuration only.

Gate: Gradle generates current bindings and compiles them against the intended shared runtime.

## Step 4: Expose APIs and compose modules

1. Read `references/runtime-api.md` for records/errors/objects, borrowed bytes, callbacks, async, custom types, and serialization.
2. Give each generated Rust object a lifetime owner; release with `close()`/`destroy()`/scoped use. Test calls after close and exception paths; cleaner timing is not resource-lifetime control.
3. Multi-module -> assign one Gradle module per Cargo crate, a unique Kotlin package per crate, and matching Cargo plus Kotlin project dependencies. Use `api` when shared types cross the public API.
4. Keep `generateBindingsForExternalCrates=false` for owned multi-module crates; enabling it duplicates shared Kotlin types. Enable only for a third-party UniFFI crate without its own Kotlin module.
5. Build all modules against the same shared-crate version. Do not pass a Kotlin foreign-trait implementation from its defining crate into another crate's functions on the documented unsupported path; it can abort the process.
6. Map expected Rust failures to typed exported errors; keep panics distinct. Retain JVM/Android API checksums and the independent contract-version check; Native has neither runtime check, and none detects every shared-crate layout mismatch.

Gate: real cross-boundary calls preserve type identity, values, errors, ownership, and any async/callback contract.

## Step 5: Build and package the target matrix

1. Read `references/gradle-targets.md`; discover effective tasks with `./gradlew :module:tasks --all`.
2. JVM debug -> host binary only. `-PreleaseBuild=true` also expands desktop target builds; provision the cross toolchains before release/publication. Rust libraries live in JVM resources, not Gobley's separate runtime-classifier JAR scheme.
3. Android -> use AGP 9 `com.android.kotlin.multiplatform.library` with `kotlin { android { ... } }`; pin NDK and deliberate debug ABIs. Release still builds all supported Android ABIs. Verify runtime/crate native libraries, host-test resources, R8 rules, and actual packaged release behavior.
4. Native -> verify generated C headers, runtime cinterop identity/commonization, static linkage, deployment floors, and device/simulator architecture. Apply the Rustup linker override only to an evidenced LLVM mismatch.
5. Publish to a disposable repository and resolve a separate consumer when publication changes. Compile-only success does not prove the shared runtime's native library is packaged or loaded.

Gate: each claimed target executes generated calls through its delivered binaries and shared runtime.

## Step 6: Verify and report

1. Run Cargo checks/tests and target-specific Kotlin checks, then actual generated calls. For the bundled JVM example, prove integer result/boundary, typed error, Unicode buffer round trip, and object destruction behavior with `interopSmoke`.
2. Multi-module -> exchange the same shared object/record through each consumer. Async/custom/borrowed APIs -> exercise relevant cancellation, lift/lower, and byte boundaries on supported platforms.
3. Inspect final native resources/JNI libraries/frameworks and resolved runtime/dependency versions; exercise release separately from debug.
4. Copy `assets/interop-report.md`; record source pins, allocator review, module graph, target/host matrix, commands/artifacts, observed behavior, and unavailable evidence.
5. Keep unsupported/unavailable paths explicitly unverified. Generation alone is not Android/Native/device execution proof.

## Error Handling

- Missing generation mode / wrong Kotlin plugin -> select one generation mode and apply KMP in the owning module.
- Contract/API mismatch -> align exact UniFFI, generator/runtime/plugin and loaded crate; regenerate/repackage instead of disabling checks.
- Crash while transferring buffers -> inspect allocator and shared-crate ABI compatibility before changing bindings.
- Duplicate shared Kotlin types -> restore one owning module and disable external-crate generation for owned dependencies.
- Callback abort across modules -> use a supported defining-module boundary; no exception handler repairs a native process abort.
- Native unresolved cinterop / already-bound RustBuffer -> check commonization, matching 1.3.1 runtime, and shared header identity.
- Missing native library / unsupported target / ABI / NDK / linker -> follow `references/gradle-targets.md`; fix the first artifact/toolchain boundary.
- Lock helper fails -> correct the selected lockfile/version graph; it cannot validate features, allocators, or runtime binaries.
