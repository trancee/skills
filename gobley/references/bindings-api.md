# Binding generation and API ownership

## Select one generation mode

**Proc-macro/library mode:** use `#[uniffi::export]`, derive the exported types, and call `uniffi::setup_scaffolding!()` at crate root. Generate from the resulting library, preferably `cdylib` so its runtime library name is inferred. Cargo package names, library target names, UniFFI namespaces, Kotlin packages, and platform filenames are distinct.

```kotlin
uniffi {
    generateFromLibrary {
        packageName = "com.example.core"
        // Set namespace/build/variant only when default selection is wrong.
    }
}
```

**UDL mode:** preserve the UDL namespace, build-script scaffolding (`uniffi::generate_scaffolding` with its build feature, or `uniffi_build::generate_scaffolding`), and `uniffi::include_scaffolding!` integration. Point `generateFromUdl { udlFile = layout.projectDirectory.file("rust/src/core.udl") }` to the real UDL. Match runtime/build/generator UniFFI versions. Mixed UDL/proc-macro exports retain UDL scaffolding: use `include_scaffolding!`, not an additional `setup_scaffolding!` in the same crate.

The Gradle plugin accepts only one generation mode per module. Read the pinned DSL before adding a second crate/interface owner.

- [UniFFI Gradle plugin](https://gobley.dev/docs/gradle-plugins/uniffi)
- [Pinned mode-selection DSL](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/build-logic/gobley-gradle-uniffi/src/main/kotlin/dsl/UniFfiExtension.kt)
- [UniFFI 0.29 tutorial](https://mozilla.github.io/uniffi-rs/0.29/tutorial/Rust_scaffolding.html)

## Manual generator branch

Prefer the Gradle-managed bindgen unless a different build system owns generated sources. Inspect the actual CLI; the live documentation's installation command is obscured by email protection and its example describes UDL mode.

```bash
cargo install gobley-uniffi-bindgen --version 0.3.7 --locked
gobley-uniffi-bindgen --help
gobley-uniffi-bindgen --library path/to/libgobley_core.so \
  --crate gobley_core --config path/to/uniffi.toml --out-dir build/bindings
```

UDL branch:

```bash
gobley-uniffi-bindgen path/to/core.udl --lib-file path/to/libcore.so \
  --crate core --out-dir build/bindings
```

`--library` takes the library as the positional source; never combine it with `--lib-file`. `--out-dir` is required in library mode. Omit `--config` when no file exists. External/UDL metadata may require `--crate-paths NAME=DIR` or `--crate-configs NAME=FILE`; inspect help before supplying them.

CLI config is a **root** TOML table (`package_name = "com.example.core"`), as used by the pinned examples; do not assume stock UniFFI's language-specific config nesting. Gradle merges TOML and DSL; [pinned merge code](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/build-logic/gobley-gradle-uniffi/src/main/kotlin/tasks/MergeUniffiConfigTask.kt) uses existing TOML scalar values before DSL fallbacks. Avoid competing owners.

Manual KMP generation requires explicit configuration; without it the standalone CLI defaults to a single-platform `main` output. For the library-mode command above, supply this root `uniffi.toml`:

```toml
package_name = "example.gobley"
kotlin_multiplatform = true
kotlin_targets = ["jvm", "android", "native"]
```

This generates common/JVM/Android/Native Kotlin plus C headers; requesting `stub` adds unsupported-target stubs. With Gradle, the plugin supplies target configuration and registers source sets/cinterop tasks. Manual generation -> own all producer dependencies, generated-source registration, runtime dependencies, and native linking explicitly.

Sources: [bindgen options](https://gobley.dev/docs/bindgen), [pinned CLI](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/crates/gobley-uniffi-bindgen/src/main.rs).

## Type and lifetime contract

- Functions -> export coarse operations; value serialization/copies happen at the FFI boundary.
- Records/enums -> derive `uniffi::Record` / `uniffi::Enum`; keep data-only values separate from live objects. `generateImmutableRecords` changes generated field mutability.
- Fallible functions -> return `Result<T, E>` with an exported error type, such as an enum deriving `thiserror::Error` and `uniffi::Error`. Confirm Kotlin catches the generated exception and preserves meaningful fields.
- Objects -> derive `uniffi::Object`, export the impl, annotate constructors. Generated proxies hold Rust `Arc` references. Use `try/finally { object.close() }`; owner-scoped UI disposal is another valid boundary. Do not call methods after close or close a shared object while another owner is using it.
- Concurrent objects/callbacks -> exported objects must meet UniFFI's `Send + Sync` contract; use appropriate Rust synchronization. Treat callback reentrancy and thread affinity as API constraints, not generated-code fixes.
- Async -> exported Rust async functions generate suspending calls. Tokio-dependent work needs an explicit runtime integration, e.g. `#[uniffi::export(async_runtime = "tokio")]` plus matching Cargo feature/dependency. Gobley's pinned async template calls Rust future cancellation when a continuation is cancelled; verify effects on separately spawned Rust work rather than assuming it stops too. Exercise cancellation and runtime shutdown; a Kotlin dispatcher does not install Tokio.

Sources: [objects and Arc ownership](https://mozilla.github.io/uniffi-rs/0.29/types/interfaces.html), [errors](https://mozilla.github.io/uniffi-rs/0.29/types/errors.html), [pinned Tokio example](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/examples/tokio-blake3-app/src/commonMain/rust/lib.rs).

## Custom/external types and serialization

Custom types require a Rust UniFFI converter plus Kotlin lift/lower expressions whose `{}` placeholder represents the source expression. Use a type available on every generated target; `java.util.UUID` is not a commonMain multiplatform mapping.

```kotlin
uniffi {
    generateFromLibrary {
        customType("Url") {
            typeName = "io.ktor.http.Url"
            imports.add("io.ktor.http.Url")
            lift = "Url({})"
            lower = "{}.toString()"
        }
    }
}
```

Add the mapped library to the owning source set; test accepted/rejected values and round-trip semantics. External types across crates need aligned package/configuration dependencies and final shared-library ownership. Avoid loading redundant component libraries when the final `cdylib` already contains them; configure `embedRustLibrary` and `cdylib_name` deliberately.

Kotlin serialization -> apply the serialization compiler plugin at the consumer's KGP version and resolve serialization runtime dependencies. Gobley detects serialization and can generate `@Serializable` data types; verify custom-type serializers and actual encode/decode behavior. Keep `omitChecksums=false`; checksum failures reveal generator/runtime drift.

Sources: [custom-type example](https://github.com/gobley/gobley/blob/0309dc04fd8dbf89eb3cf9cd796c746b1979cce2/examples/custom-types/build.gradle.kts), [bindgen configuration](https://gobley.dev/docs/bindgen#bindgen-configuration), [external types](https://mozilla.github.io/uniffi-rs/0.29/types/remote_ext_types.html).
