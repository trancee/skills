# Source build and target toolchains

Baseline: [v5.12.0 BUILDING.md](https://github.com/aws/aws-lc/blob/v5.12.0/BUILDING.md), [CMakeLists.txt](https://github.com/aws/aws-lc/blob/v5.12.0/CMakeLists.txt), and [INCORPORATING.md](https://github.com/aws/aws-lc/blob/v5.12.0/INCORPORATING.md). Read the chosen revision rather than carrying baseline flags into another release.

## 1. Resolve prerequisites and pin

1. CHECK C/C++ compilers, CMake, Ninja, Perl, and Go. Baseline CMake source requires 3.5 although prose still says 3.0; Go minimum is 1.20. Prefer current supported tools. Windows needs a suitable MSVC developer environment and NASM; prefer Ninja because upstream Visual Studio-generator guidance is inconsistent and not regularly tested.
2. CHECK `cmake --version`, `ninja --version`, `go version`, `perl -v`, and the compiler identity. Specify `GO_EXECUTABLE`, `PERL_EXECUTABLE`, or `CMAKE_ASM_NASM_COMPILER` if detection misses installed tools.
3. For a new ordinary build, acquire the reviewed pin:

```bash
git clone --branch v5.12.0 --depth 1 https://github.com/aws/aws-lc.git aws-lc-src
git -C aws-lc-src rev-parse HEAD
# Authored baseline: cd481c207e38f06aeb5766f4a1cdfce10a4c0af8
```

Keep existing project pins unless upgrading is requested. Do not select temporary project-specific branches as supported release branches. FIPS deployments choose their policy-matched module revision first, not this mainline example.

## 2. Configure, build, install

Set `AWSLC_PREFIX` to an absolute private installation directory, and `JOBS` to the host's chosen concurrency. Run from the directory containing `aws-lc-src`:

```bash
cmake -S aws-lc-src -B aws-lc-build -GNinja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="$AWSLC_PREFIX" \
  -DCMAKE_INSTALL_LIBDIR=lib
cmake --build aws-lc-build --parallel "$JOBS"
cmake --install aws-lc-build
```

The ordinary default is static. Shared -> add `-DBUILD_SHARED_LIBS=ON`. Development assertions -> use `Debug` deliberately. `CMAKE_INSTALL_LIBDIR=lib` avoids distribution `lib64` ambiguity; preserve the actual layout if choosing another directory. Install into a new prefix when comparing releases/build modes.

| Requirement | Baseline choice | Consequence |
|---|---|---|
| crypto only | `-DBUILD_LIBSSL=OFF` | no libssl or libssl pkg-config module |
| libraries without CLI | `-DBUILD_TOOL=OFF` | no bssl tool |
| production-only artifact | `-DBUILD_TESTING=OFF` | no upstream test targets; verify a separate test build |
| pre-generated inputs | `-DDISABLE_GO=ON` and/or `-DDISABLE_PERL=ON` | reduced generation/tests; not FIPS |
| size-sensitive | `-DOPENSSL_SMALL=1` | algorithm/assembly size-performance tradeoffs; measure linked binary |
| host cohabitation, Linux/BSD | `-DENABLE_DIST_PKG=ON` | suffixed libraries and `include/aws-lc/openssl` |
| OpenSSL-name consumers of dist build | `-DENABLE_DIST_PKG_OPENSSL_SHIM=ON` with dist mode | upstream unsuffixed symlinks/pkg-config interface; keep private |

Source configuration updates version/FIPS-related public headers when `ENABLE_SOURCE_MODIFICATION=ON` (default). A disposable source copy preserves the original checkout while allowing the generated install headers to match. Inspect artifacts if disabling modification; do not install non-FIPS headers beside a FIPS build accidentally.

## 3. Run the right upstream suite

```bash
cmake --build aws-lc-build --target run_tests --parallel "$JOBS"
```

This baseline target invokes Go tests, native tests, and the TLS blackbox runner when libssl is enabled. It is not equivalent to CTest listing a few entries. From the source root, the native harness can be run separately:

```bash
go run util/all_tests.go -build-dir /absolute/path/to/aws-lc-build
```

A native binary accepts GoogleTest filtering; record both the filter and test count. `crypto/crypto_test` and `ssl/ssl_test` are examples, not the entire suite. Without Go, inspect/run `run_minimal_tests` and disclose that blackbox/Go coverage is absent. Cross-built binaries must execute on the target or an appropriate emulator, not the host.

## 4. Cross-compile with one SDK per build

1. SELECT the target OS, ABI, minimum OS/API, SDK, compiler/sysroot, and static/shared packaging required by the consumer. Use its existing CMake toolchain file and separate build directory.
2. KEEP Go and Perl as host tools; do not accidentally substitute target executables for generators.
3. Android -> use the installed NDK's CMake toolchain, e.g.:

```bash
cmake -S aws-lc-src -B aws-lc-android-arm64 -GNinja \
  -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-21 \
  -DCMAKE_BUILD_TYPE=Release
cmake --build aws-lc-android-arm64 --parallel "$JOBS"
```

Choose the consumer's actual API level (arm64 requires at least 21); inspect current NDK guidance rather than copying the upstream document's old NDK/debugger examples.

4. iOS on Apple tooling -> configure `CMAKE_OSX_SYSROOT=iphoneos`, `CMAKE_OSX_ARCHITECTURES=arm64`, and the consuming deployment target. Build device and simulator slices separately; AWS-LC's baseline does not support a multi-architecture CMake invocation. Linux-to-iOS needs a real Apple-target toolchain/SDK; iOS flags alone do not provide one.
5. CHECK artifact architecture and perform a linked operation on the actual target. A successful cross-build is not target runtime evidence.

## 5. Diagnose at the first failing stage

- Missing assembly capability -> verify assembler/toolchain/architecture. Use documented assembly exclusion flags only for the intended target and measure impact; avoid blanket no-assembly workarounds.
- Illegal instruction -> compare actual target CPU features with compile-time assumptions. `OPENSSL_STATIC_ARMCAP*`/`-march` may remove runtime fallbacks; compile for the supported deployment baseline.
- Multiple crypto implementations in one process -> inspect symbols and load boundaries. Custom `BORINGSSL_PREFIX` requires a maintained symbol list and generated headers; it cannot combine with symbol versioning. Treat it as an explicit integration project, not an automatic fix.
- Shared Windows consumer -> define `BORINGSSL_SHARED_LIBRARY` consistently and make the matching DLL available to the process.

Sources: [build/test/platform flags](https://github.com/aws/aws-lc/blob/v5.12.0/BUILDING.md), [effective CMake validation](https://github.com/aws/aws-lc/blob/v5.12.0/CMakeLists.txt), [Go tool detection](https://github.com/aws/aws-lc/blob/v5.12.0/cmake/go.cmake).
