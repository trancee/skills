# Platform and runtime troubleshooting

Read the [cross-compilation guide](https://gobley.dev/docs/cross-compilation-tips) for the failing platform; historical version examples are not current toolchain recommendations. Preserve the original failure, effective target triple, compiler/linker invocation, selected binary, and runtime architecture before changes.

## Rust target or linker unavailable

`rustup target add TRIPLE` provides prebuilt Rust standard libraries, **not** the platform SDK/C compiler/linker. Verify `rustc --version --verbose`, target installation, and the target-specific linker.

- Android -> configured SDK/NDK, ABI, API level, and NDK clang sysroot; inspect `CC_<target>`/`BINDGEN_EXTRA_CLANG_ARGS_<target>` before overriding plugin-generated environment.
- Apple -> selected full Xcode/SDK and target arch/environment. Set `DEVELOPER_DIR` process-locally when pinning Xcode.
- Linux cross-build on Windows/macOS -> dedicated GCC or Zig cross linker. Use a project-scoped Cargo target linker configuration and a wrapper that forwards arguments (`"$@"` on POSIX), rather than passing GNU flags to Apple's linker.
- Windows MSVC ARM64 -> install the ARM64/ARM64EC compiler/linker toolchain, not 32-bit ARM. MinGW Windows ARM is not a supported Gobley target.

Tier-3 Rust targets may require pinned nightly, `rust-src`, and `-Zbuild-std`; query target tier for the selected Rust version instead of assuming tvOS/watchOS remain tier 3 forever. Configure both build/check tasks as needed. Do not add nightly flags to every target.

## Apple deployment and LLVM mismatch

`___chkstk_darwin` or other unavailable symbols can reflect inconsistent deployment floors between Rust and C/C++ objects. Align Rust environment with the supported application/framework minimum:

```kotlin
import gobley.gradle.cargo.dsl.appleMobile

cargo {
    builds.appleMobile {
        variants {
            buildTaskProvider.configure {
                if (rustTarget.cinteropName == "ios") {
                    additionalEnvironment.put("IPHONEOS_DEPLOYMENT_TARGET", "16.0")
                }
            }
        }
    }
}
```

16.0 is an example, not a universal floor. Likewise align `TVOS_DEPLOYMENT_TARGET`, `WATCHOS_DEPLOYMENT_TARGET`, and macOS policy where applicable. Inspect actual compiler flags; do not raise one dependency's minimum beyond the app's declared support unnoticed.

LLVM-related linker failures -> compare Rust LLVM, Kotlin/Native LLVM, and Apple linker. For a proven Kotlin/Native linker mismatch, consumers can apply `dev.gobley.rust` and use `gobley.gradle.rust.dsl.useRustUpLinker()` on the failing compilation. It requires a Rustup-distributed linker; it is not a universal replacement for Apple SDK/toolchain prerequisites. Validate compatible toolchain changes instead of randomly downgrading Rust.

Sources: [Rust linker plugin](https://gobley.dev/docs/gradle-plugins/rust), [Rust iOS platform support](https://doc.rust-lang.org/stable/rustc/platform-support/apple-ios.html).

## Android release, C++ runtime, and 16 KB pages

`UnsatisfiedLinkError` -> distinguish absence/ABI mismatch, dependency loader failure, missing exported symbols, and JNA reflection obfuscation. Inspect APK/AAR native entries and release dependency resolution. Keep generated JNA rules enabled unless equivalent consumer rules are owned and tested elsewhere.

C++ symbols such as `__cxa_pure_virtual` -> inspect actual link arguments and selected `libc++_static`/`libc++_shared`; use one consistent runtime and package shared dependencies where required.

For 16 KB devices, verify **all** native dependencies including JNA and C++ runtime. Gobley documentation requires JNA >=5.17; 0.3.7 prefers 5.18.1, but consumer constraints may select something else. NDK r28+ defaults to compatible ELF alignment; still inspect the final artifacts and APK ZIP alignment following [Android's current guide](https://developer.android.com/guide/practices/page-sizes).

Earlier supported NDK -> add the required linker flags without clobbering existing Rust flags. `-C link-args=-Wl,-z,max-page-size=16384` is Gobley's documented example. Confirm `llvm-readelf -lW LIBRARY` load-segment alignment and test on a 16 KB emulator/device. ELF alignment alone does not establish final APK/package compatibility.

Preserve exported UniFFI symbols and debug-symbol artifacts. Prefer letting AGP strip the final app rather than blindly stripping a producer AAR. Verify release linkage/loading after LTO or strip changes; retain symbols needed for crash diagnosis under the release policy.

## Runtime ABI or generated API mismatch

- Checksum/version failure -> align generator and actual linked/loaded crate/UniFFI/features, regenerate and repackage. Keep checksum verification enabled.
- Crate metadata absent -> correct library target and scaffolding; Kotlin package rename does not repair missing Rust metadata.
- JVM tests pass, published consumer fails -> inspect runtime classifier JARs, native entries, dependent libraries, and consumer Rust plugin. Avoid relying on `jna.library.path` to hide an incomplete published artifact.
- JS/Wasm compile succeeds then calls throw -> stubs are compile-time compatibility only; no working UniFFI implementation is supplied.
- Closed object/callback races -> correct ownership, reference lifetime, synchronization, and cancellation at the API boundary; regenerated code is not the fix.
- Disk exhaustion -> measure Cargo/Gradle output and prune only owned disposable outputs after dependent processes finish. Avoid the upstream guide's blanket deletion of global Gradle caches as a default repair.
