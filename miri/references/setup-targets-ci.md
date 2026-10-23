# Toolchain, target, and CI control

Baseline: upstream [Miri README at 89224698f215583aef7e10554598cd0f5445a455](https://github.com/rust-lang/miri/blob/89224698f215583aef7e10554598cd0f5445a455/README.md); flags are unstable and the rustup component may differ from current master. Verify the actual installed versions and diagnostics before copying a master-only flag.

## Install without migrating the consumer

1. Read `rust-toolchain.toml`/`rust-toolchain`, Cargo manifests, lockfile, `.cargo/config.toml`, existing CI, target/features and native dependencies. Review build scripts/proc macros before execution. Miri isolation applies to interpreted code, not Cargo's build-time code, and is not a security sandbox.
2. Install rustup from the [official instructions](https://rust-lang.github.io/rustup/installation/index.html) if absent. Distro Cargo/rustc alone cannot provide `cargo +nightly miri`; `cargo install miri` is not the component installation route. On Windows use the rustup Windows installer; on Linux/macOS review the official installer before running it. A host toolchain may need its usual native linker/build prerequisites for build scripts.
3. Install a supported nightly with both components, explicitly selecting it rather than changing global defaults:
   ```bash
   rustup toolchain install nightly-2026-10-23 --profile minimal --component miri,rust-src
   cargo +nightly-2026-10-23 miri setup
   rustc +nightly-2026-10-23 -Vv
   cargo +nightly-2026-10-23 -V
   cargo +nightly-2026-10-23 miri --version
   ```
   The date is the exercised baseline, not a requirement to downgrade an existing compatible pin. Preserve a stable production/MSRV toolchain and use a separate nightly lane. Record any required compiler feature/dependency incompatibility instead of silently rewriting the manifest or lockfile.
4. Component unavailable -> consult [component history](https://rust-lang.github.io/rustup-components-history/) for the **host** triple; select a dated nightly providing Miri. For a deliberately floating lane, `rustup toolchain install nightly --allow-downgrade --profile minimal --component miri,rust-src` searches backward. Record the resolved date/commit; floating `nightly` alone is not reproducible.
5. Setup builds a matching interpreter standard library and may fetch dependencies. Run it explicitly before tests so setup failures are distinct. Leave `MIRI_SYSROOT` and `MIRI_LIB_SRC` unset unless intentionally managing a custom sysroot. Compiler/sysroot mismatch -> inspect overrides, then `cargo +nightly-2026-10-23 miri clean` and repeat setup; do not delete unrelated consumer artifacts.

For a disposable installation, set `RUSTUP_HOME` and `CARGO_HOME` to owned scratch directories before installing rustup, use `--default-toolchain none --no-modify-path`, and retain those variables plus `CARGO_HOME/bin` on PATH for every command. `XDG_CACHE_HOME` can isolate Miri's cache on Linux. Remove only owned scratch directories after collecting evidence.

## Select real targets and tests

Run from the consumer's Cargo workspace, using its actual package, target and feature names:

```bash
cargo +nightly-2026-10-23 miri test --locked -p actual-package --lib
cargo +nightly-2026-10-23 miri test --locked -p actual-package --test actual-integration-test test_filter
cargo +nightly-2026-10-23 miri run --locked -p actual-package --bin actual-binary -- app-argument
```

Cargo selection flags go before `--`; libtest/binary arguments go after it. For an exact unit test, supply its full path, e.g. `tests::raw_owner`, then `-- --exact --nocapture`. Check actual executed/ignored counts; a successful filter matching zero tests proves nothing. Enumerate workspace packages, integration tests, doctests and feature combinations separately; one successful library test invocation is not workspace-wide coverage. Use `--locked` only with the reviewed lockfile; generate/review one deliberately if absent.

The bundled helper runs owned fixture controls, not the consumer suite:

```bash
python3 scripts/smoke.py --toolchain nightly-2026-10-23
python3 scripts/smoke.py --toolchain nightly-2026-10-23 --target s390x-unknown-linux-gnu
```

Resolve the helper from the activated skill root. It creates/removes a standalone temporary Cargo package; tests ownership recovery, boundary slices and wire endianness; then runs ignored Miri-only use-after-free and leak controls separately. A compile/setup failure cannot satisfy a negative control. It clears interpreter/compiler override flags and custom sysroot variables; record separate flags when testing consumer behavior. The intentional controls are not production regression tests and must not be copied into an ordinary native test suite.

## Cross-interpretation

```bash
cargo +nightly-2026-10-23 miri setup --target s390x-unknown-linux-gnu
cargo +nightly-2026-10-23 miri test --target s390x-unknown-linux-gnu
```

Miri interprets the target; a cross-linker/native runner is not the normal requirement. It builds an interpreter sysroot from `rust-src`. Build scripts/native dependencies can still introduce host or cross-toolchain requirements. Big-endian s390x exposes wire-format/native-endian assumptions; retain architecture-independent expected values rather than changing expected outputs to match the host.

Upstream tests Tier 1 targets and s390x; OS shim support is strongest on Linux, generally comparable on macOS, weaker on Windows. `--target x86_64-unknown-linux-gnu` can improve interpreted API support on Windows but does not validate Windows-specific branches. Use the actual target for platform-specific claims. For SIMD, distinguish compiled target features from supported interpreter intrinsics; unsupported intrinsics are coverage gaps, not permission to infer native correctness.

## Continuous integration

Add a separate job to existing CI after source checkout and project-specific setup. Retain the repository's approved action pins, dependency credentials policy and working directory. The command sequence is:

```bash
rustup toolchain install nightly-2026-10-23 --profile minimal --component miri,rust-src
cargo +nightly-2026-10-23 miri setup
cargo +nightly-2026-10-23 miri test --locked
```

Use the consumer's explicit package/target/features where the full suite is unsupported or too costly, and publish exclusions. Key any cache by actual nightly, host/interpreted target, lockfile and relevant build flags; keep Miri artifacts separate from native artifacts. Keep a reproducible pinned lane; evaluate nightly updates in a controlled change rather than hiding new failures behind an automatic downgrade or permanent allowed-failure job.

Nextest is optional, not the default: `cargo +nightly-2026-10-23 miri nextest run` requires compatible cargo-nextest. Separate processes permit parallelism and independent failures, but can recompile the crate once per test, do not detect races between tests sharing a process, and do not cover doctests. Preserve ordinary `cargo miri test` where those boundaries matter.
