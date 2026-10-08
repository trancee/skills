# Runtime API, ownership, and composition

Verified at Ubique 1.3.1, commit `b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300`. Apply the core procedure's version contract first.

## Consumer-facing types and lifetime

- Rust functions become Kotlin functions; exported objects become generated classes/interfaces. `Result` failures become typed generated exceptions. Rust panics and unexpected callback errors use `InternalException`, not the expected error type.
- Records/enums are Kotlin value representations, serialized on each FFI crossing. Mutating a Kotlin copy does not mutate Rust. Strings, lists/maps, byte vectors, errors, and optionals also use conversion/buffer paths; do not describe the integration as blanket zero-copy.
- Objects cross as Arc-backed handles. Give each returned object an owner and call `close()`/`destroy()`, or generated `use {}`. Generated `Disposable` also covers records/enums containing owned objects. Account for ownership on return, exception, and cancellation paths.
- `destroy()` is idempotent. Calls after destruction reject with `IllegalStateException`; in-flight calls retain a cloned handle until completion. A cleaner is fallback reclamation, not deterministic release of resources.
- JVM uses Java Cleaner with a JNA fallback; Android uses SystemCleaner on API 34+ with a fallback; Native uses createCleaner/once-only cleanup. Generated packages declare their own Disposable/use/NoHandle surface while common runtime helpers also exist.
- `NoHandle` is the construction marker for interface fakes; invoking their native implementation fails. It is not a substitute for a missing Rust library.

Sources: [functions/objects](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/functions-and-objects/), [records/enums](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/records-and-enums/), [object internals](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/internals/objects-and-handles/).

## Buffers and borrowed bytes

`RustBuffer` carries capacity, length, and a pointer. Allocation uses the shared runtime's `ffi_uniffi_runtime_rustbuffer_alloc`; the receiving crate may free the buffer. Every participating crate/dependency must use Rust's default allocator. Audit actual sources/features for custom global allocators; neither Cargo.lock nor API checksum checks proves allocator compatibility.

Ordinary `Vec<u8>` uses serialized ByteArray conversion. Borrowed `&[u8]` uses `ForeignBytes`/`withForeignBytes`: Native pins the ByteArray for the call; JVM/Android copy into native memory for the call. Rust must not retain the borrowed address. Zero-length and non-ASCII/binary boundaries need actual consumer checks when changed.

## Callback and async boundaries

- Callback interfaces/`with_foreign` traits register vtables and keep Kotlin implementations alive in handle maps. Handle clone/free and lift ownership differ from ordinary value serialization; preserve the generated converters rather than substituting ad-hoc numeric handles.
- Kotlin implementations of a foreign trait declared in crate A can go to A's functions, but **not** another crate B's functions: each library has its own vtable static and B's copy is uninitialized. This documented 1.3.1 limitation aborts the process; exit status is platform-dependent and an exception handler cannot recover. Rust implementations are supported. Track [issue #35](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/issues/35).
- Exported Rust async functions become suspend calls. `uniffiRustCallAsync` polls the Rust future on Dispatchers.IO, routes completion/error conversion, handles cancellation, and frees the future in finally. Future poll values are ready=0/maybe-ready=1, not Boolean success/failure.
- Foreign async calls use runtime-owned coroutines/foreign-future handle maps; dropping the Rust foreign future cancels its job. The implementation uses GlobalScope internally; consumer code should still supply its own structured lifetime rather than imitate that implementation detail.
- Exercise cancellation before/after readiness, typed error propagation, and callback lifetime where applicable. A successful synchronous call is not async/callback proof.

Sources: [callback guide](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/callbacks/), [async guide](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/async/), [multi-module limitation](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/multi-module/#limitations).

## Custom types and serialization

Custom UniFFI types default to Kotlin typealiases backed by the builtin converter. A root-level `[custom_types.<Name>]` TOML table selects `type_name`, `imports`, `lift`, and `lower`; `{}` is the substituted expression. For example, a String-backed URL can use `lift = "Url({})"` and `lower = "{}.toString()"` when that Url type exists in commonMain. `into_custom`/`from_custom` are accepted aliases. Verify both directions and failure behavior against the actual Rust builtin representation.

`generate_serializable_records = true` opts records and eligible enums into kotlinx.serialization; object-containing enums are excluded. `skip_serializer_for` excludes named types. Apply the Kotlin serialization compiler plugin and a serialization dependency in the consumer. Serialized field names use Rust names on encode and accept Kotlin names on decode via JsonNames. 1.3.0 fixes missing variant serializers when a variant starts with a custom/external type.

Sources: [custom types](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/custom-types/), [serialization](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/serialization/), [TOML options](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/configuration/uniffi-toml/).

## Multi-module invariants and dependency edits

1. Keep one Kotlin owner/package per Cargo crate and `generateBindingsForExternalCrates=false` for owned dependencies. A third-party UniFFI crate without a Kotlin module uses the separate external-types branch.
2. Build every module against identical shared-crate source/version/features and the same shared runtime. Each library embeds the shared crate; mismatched layouts can silently corrupt memory, and runtime checks do not detect them all.
3. Shared records serialize at each crossing; objects retain shared type identity and route through compatible shared-crate code. This is composition, not elimination of all transfer costs.
4. Preserve shared `common.h` identities across runtime and generated headers. Native static libraries contain repeated shared-crate symbols; the plugin handles multiple definitions on Linux/Windows and the Apple linker accepts them.
5. Mirror Cargo dependencies in Kotlin dependencies; use `api` when the shared types occur in public signatures.

For already configured sibling modules named shared and consumer, merge these dependency entries into the owning blocks:

```toml
# consumer/Cargo.toml
[dependencies]
uniffi = "=0.32.0"
ubique-shared = { path = "../shared" }
```

```kotlin
// consumer/build.gradle.kts
kotlin {
    sourceSets.commonMain.dependencies {
        api(project(":shared"))
    }
}
```

The shared Cargo crate needs `lib` for Rust dependents, plus platform crate types. Include both modules in Gradle settings and the Cargo workspace when applicable. Each uses library generation and a unique package map. Export functions taking/returning the actual shared types; do not redeclare those types in the consumer. An app uses `implementation(project(":consumer"))`; the public shared dependency is transitive.

Prove same-object transfer and shared-record value equality through actual generated calls, then close owned objects. The complete [upstream fixture](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/tree/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/tests/uniffi/multi-module) includes object methods omitted by guide snippets.

Sources: [multi-module guide](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/multi-module/), [external types](https://ubiqueinnovation.github.io/uniffi-kotlin-multiplatform-bindings/guide/features/external-types/).

## Runtime checks and failure probes

JVM/Android lazy `UniffiLib.INSTANCE` initialization checks per-function API checksums and the independent UniFFI contract version, then initializes dependent crates' vtables. `omit_checksums=true` skips API checksums only; contract-version checking remains. Native has neither runtime check because it statically links. Correct mismatched inputs/source revisions and regenerate/repackage; disabling checks is not a repair.

Select probes for changed paths: typed overflow vs panic, Unicode buffer round trip, post-close rejection/idempotent destruction, shared-record equality/object identity, and stale signature/version rejection. Probe a crash-prone unsupported boundary only in an isolated disposable subprocess, never inside the application or the test runner process.

## Runtime-maintenance lookup

Read the relevant file in the [pinned runtime source](https://github.com/UbiqueInnovation/uniffi-kotlin-multiplatform-bindings/tree/b819fb4ea33d0ddeb3f1970e5b0d7367c3c7d300/runtime/src) when editing/debugging runtime code:

| Boundary | Symbols / source |
| --- | --- |
| Common ownership | runtime.common.kt: Disposable, NoHandle, InternalException, expect Pointer |
| Callback handles | HandleMap.kt: UniffiHandleMap insert/get/remove/clone; odd Kotlin handles |
| Lift/lower | platform FfiConverterTemplate.kt; FfiConverter<K,T>, FfiConverterRustBuffer<K> |
| Buffer ownership | platform RustBufferTemplate.kt; RustBufferHelper, ForeignBytes, withForeignBytes |
| Error/call status | Helpers.kt, runtime.jvm.kt/runtime.native.kt; UniffiRustCallStatus, uniffiRustCallWithError |
| Async cancellation | Async.kt; uniffiRustCallAsync, continuation/foreign-future handle maps |
| Callback ownership | CallbackInterfaceRuntime.kt; callback lift borrows, with_foreign lift removes/transfers |
| Reclamation | ObjectCleanerHelper.kt; UniffiCleaner |

JVM/Android use JNA structs/pointers/callbacks; Native uses cinterop aliases/staticCFunction. The platform copies are hand-written, and the shared runtime Rust crate only supplies scaffolding/buffer functions. Runtime ABI changes require all generated consumers and platform copies to remain aligned.
