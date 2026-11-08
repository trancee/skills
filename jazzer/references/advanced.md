# Configuration, detectors, JNI and source builds

Sources: [released options](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/docs/arguments-and-configuration-options.md), [advanced documentation](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/docs/advanced.md), [contributor instructions](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/CONTRIBUTING.md), [BugDetectors API](https://codeintelligencetesting.github.io/jazzer-docs/jazzer-api/com/code_intelligence/jazzer/api/BugDetectors.html).

## 1. Resolve actual effective configuration

Precedence increases from default -> `META-INF/MANIFEST.MF` Jazzer attribute -> `JAZZER_SOME_OPT` environment -> `jazzer.some_opt` JVM property -> JUnit configuration parameter -> standalone `--some_opt`. Inspect every applicable layer before blaming the target.

- Check `--help` from the actual release and distinguish standalone-only, fuzz-only and environment-only options. Doc strings may lag (for example native/HWASan defaults); the selected runtime is authoritative.
- Scope coverage with `--instrumentation_includes`/`excludes` but retain relevant implementation dependencies. Coverage excludes and `--custom_hook_includes`/`excludes` are different controls. A target wrapper being instrumented does not prove deeper code coverage.
- Try `-use_value_profile=1` for hard comparison/string gates after verifying the relevant code is reached. `--trace` controls coverage/compare/division/other feedback; do not turn hooks off to suppress a finding or mislabel no instrumentation as successful fuzzing.
- `--keep_going=N` can collect multiple distinct findings within a budget; `--keep_going=0` relies on another stop limit. Dedup tokens group stacks for triage, not necessarily unique root causes. Ignore/detector exclusion requires an evidenced reason and must not become a permanent bypass for an unfixed defect.
- Autofuzz and Jazzer's internal JaCoCo coverage export are deprecated in this release documentation. Prefer explicit targets/typed mutation and a compatible standalone JaCoCo reporting workflow when detailed coverage is required; verify instrumentation coexistence rather than conflating fuzzer feature counters with source line coverage.

## 2. Triage built-in JVM bug detectors

1. Reproduce the reported SSRF/path traversal/command injection or other detector finding using the original target and config. Preserve stack/token/artifact and identify the reachable application call site and trust boundary.
2. Detectors are hooks, not a process sandbox. Fuzzed code can still read/write files, launch processes or access networks. Use an authorized isolated workspace, no secrets, controlled resources, and task-owned filesystem/network targets.
3. For legitimate controlled network/path operations, inspect the release's `BugDetectors` configuration API and narrowly authorize the test resource with a scoped lifetime. Do not globally disable SSRF/path checks, enable permissive-before-configuration mode casually, or claim benign execution solely because a detector was disabled.
4. Custom `@MethodHook` implementations belong in separate JARs on the classpath so Jazzer can append them to the bootstrap loader; load classes with `--custom_hooks` or a `Jazzer-Hook-Classes` manifest attribute. Confirm hook signatures/API compatibility and bootstrap visibility against the selected release.
5. Replacing checksums/randomness with hooks may reach deeper logic but changes semantics. Make that boundary explicit and verify any discovered issue without the bypass where possible. Do not turn a hook-only behavior into an unqualified production exploit claim.

## 3. Instrument native code only for a JNI target

- Build reachable native libraries with `-fsanitize=fuzzer-no-link`; coverage hooks alone are not ASan/UBSan.
- ASan build: `-fsanitize=fuzzer-no-link,address`; launch with `--asan`. UBSan build: `-fsanitize=fuzzer-no-link,undefined` plus `-fno-sanitize-recover=all` to fail on reports; launch with `--ubsan`.
- Match compiler and runtime: Jazzer uses the clang on PATH unless `CC` selects the compiling toolchain; `JAZZER_NATIVE_SANITIZERS_DIR` can point to available matching runtimes. Preserve debug symbols and native build identity for replay.
- Preloading into the JVM has platform constraints; macOS Gatekeeper/runtime restrictions are not invitations to weaken host security. LeakSanitizer is disabled because JVM GC creates excessive false positives. Treat additional sanitizer/platform support as release-specific, not a guarantee.
- Confirm native coverage and a real known native report before claiming JNI fuzzing works. A Java-only probe does not verify native sanitizer integration.

## 4. Build Jazzer only when release artifacts do not suffice

Use a clean checkout of `v0.30.0` or another explicitly recorded commit. Upstream specifies Bazelisk/the `.bazelversion` Bazel, Clang9+ or full Xcode on macOS; GCC with `--repo_env=CC=gcc` is untested upstream. From the Jazzer source root:

```bash
bazel run //:jazzer -- --help
bazel build //:jazzer_release
bazel test //...
```

The release target produces `bazel-bin/jazzer_release.tar.gz`. Honor that checkout's toolchains/dependency requirements; source build may download significant dependencies. Default tests exclude `dangerous` tags; do not clear test tag filters without explicit authorization and an adequate isolated environment, because tests can execute arbitrary commands or contact random addresses.

Android builds exist upstream but require separate SDK/NDK/ART setup and are not this skill's desktop JVM workflow. For internal debug runs use documented Bazel debug config; for external JVM debugging use an authorized local JDWP listener and inspect it rather than exposing an unauthenticated debugger publicly.

DONE: effective options, hook/detector semantics, native coverage and source-build outputs are individually evidenced; paths not exercised stay explicit verification limits.
