---
name: miri
description: "Installs, runs, and troubleshoots Miri for Rust undefined-behavior detection. Use when checking unsafe Rust, pointer provenance or aliasing, uninitialized or misaligned memory, data races, weak-memory behavior, cross-target execution, or Miri CI and unsupported-operation failures. Don't use for proving universal soundness, benchmarking native performance, checking arbitrary C/C++ FFI, or general Rust linting."
compatibility: "Requires rustup and a nightly providing miri/rust-src; exercised baseline nightly-2026-10-23 on Linux x86-64. Flags and aliasing models are experimental. Target OS/FFI support varies. Smoke helper requires Python 3.9+ and an installed toolchain; setup may download dependencies. Miri isolation is not a security sandbox."
metadata:
  category: "testing-quality"
  source: "https://plf.inf.ethz.ch/research/popl26-miri.html"
  sourceVersion: "POPL26 Miri DOI 10.1145/3776690; rust-lang/miri@89224698f215583aef7e10554598cd0f5445a455; rustup nightly-2026-10-23; inspected 2026-10-23"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-10-23T16:47:57+00:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-10-23T16:57:51+00:00"
---

# Miri: dynamic undefined-behavior detection for Rust

Resolve bundled resources from the activated skill root; run Cargo commands from the consumer's workspace. Follow the [upstream Miri documentation](https://github.com/rust-lang/miri/) matching the installed nightly, not assumed stable flag behavior.

## Step 1: Define the checked execution and trust boundary

1. Identify the package, public API/unsafe contract, tests or binary, Cargo features, target, inputs and concurrency behavior. Read repository instructions, toolchain files, Cargo manifests/lockfile/configuration and existing Miri CI before changing them.
2. Distinguish UB detection, experimental aliasing/provenance policy, additional leak checking, and unsupported-operation diagnosis. Read `references/research-scope.md` when interpreting the supplied POPL26 page, soundness claims, research artifact, or tool limits.
3. Treat a clean run as evidence about selected executions under the recorded model/configuration, not proof of a sound library, exhaustive schedules, arbitrary native FFI, or future-compiler compatibility.
4. Review Cargo build scripts, proc macros and dependencies before executing them. Miri's default host isolation is deterministic API emulation, not a security sandbox. Keep real secrets and cryptographic key generation out of interpreted tests.

Gate: the intended behavior, actual execution coverage, tool/model assumptions and host-code trust are explicit.

## Step 2: Establish a reproducible nightly

1. Read `references/setup-targets-ci.md` for rustup installation, component availability, package/target selection, cross-interpretation and CI. Preserve the production/MSRV toolchain; use an explicitly selected Miri nightly rather than a global override.
2. Install a deliberate nightly with `miri` and `rust-src`, run `cargo +nightly-2026-10-23 miri setup`, and record `rustc -Vv`, Cargo and Miri versions with the same selector. Substitute the consumer's compatible pin consistently; the shown date is the verified baseline.
3. Optional tool sanity check -> run the bundled helper from the skill root:
   ```bash
   python3 scripts/smoke.py --toolchain nightly-2026-10-23
   ```
   Require three positive tests to pass, a dangling-pointer UB diagnostic for the deliberate use-after-free control, and a separate memory-leak rejection. The helper removes its temporary package and rejects compile/setup failures as evidence. It tests the tool, not the consumer code.

Gate: the selected component builds its interpreter sysroot and executes a real test; setup failure is not a program verdict.

## Step 3: Run the consumer path without weakening checks

1. Select an existing targeted test first, then the relevant aggregate/package/feature lanes:
   ```bash
   cargo +nightly-2026-10-23 miri test --locked
   ```
   Use actual package/integration-test/binary selectors from the setup reference. Check executed/ignored counts; a zero-match filter does not validate the path. Run binaries via `cargo +nightly-2026-10-23 miri run` with real input/output assertions when appropriate.
2. Retain existing meaningful assertions and exercise safe API callers capable of exposing the unsafe implementation's boundary, ownership, initialization, drop or concurrency errors. Native tests and Clippy complement but do not replace interpretation.
3. Capture the first failure, exit code, full diagnostics, features, seed and target before editing. Classify it using `references/diagnostics-exploration.md`; unsupported APIs, isolation denial, build failures and timeouts do not establish UB or acceptance.
4. Limit Miri-specific exclusions to genuinely unsupported boundaries, explain each exclusion, and preserve separate native/integration coverage. Never bypass a known unsafe path merely to obtain a passing Miri lane.

Gate: the intended tests actually execute with checks enabled; every failed or excluded path has an accurate classification.

## Step 4: Diagnose, repair and broaden evidence

1. Read `references/diagnostics-exploration.md` for tracing allocations/pointer tags, provenance, aliasing, races, leak policy, host access and seeded exploration.
2. Minimize the same counterexample and repair the production invariant at its source. Keep input, target, features, nightly, model and flags fixed for failing-before/passing-after evidence. A flag disabling the detector is not a repair.
3. Expand relevant coverage deliberately: bounded `-Zmiri-many-seeds=0..4`, a reproduced single seed, big-endian `s390x-unknown-linux-gnu`, alternative experimental aliasing model, strict-provenance policy or layout randomization. Record each configuration separately and retain the original failure when comparing models.
4. Keep a consumer regression protecting the repaired contract; run it under Miri and natively, followed by the relevant wider suite. Restore normal checks and remove temporary tracing/scaffolds.

Gate: the original invalid execution is fixed under unchanged checking, and remaining inputs/schedules/platform/FFI gaps are explicit.

## Step 5: Integrate and report

1. Follow the setup reference's CI branch for an explicitly pinned nightly, separate setup/test steps, consumer package/feature selectors, cache identity and documented exclusions. Use optional Nextest only with its process-boundary/doctest limitations understood.
2. Copy `assets/run-report.md`; fill exact versions, configuration, commands, executed/ignored tests, exit codes, diagnostics, fix evidence and untested boundaries. Distinguish a leak-policy rejection or unsupported operation from a UB counterexample.
3. State only the evidence obtained. More seeds, a research coverage claim, or a CI badge cannot certify all safe clients or all possible executions.

## Error Handling

- Missing `cargo miri` -> check rustup proxy PATH and selected nightly's installed components; install the component, not a similarly named Cargo package.
- Missing Miri for a nightly -> consult host component history; deliberately choose and record a compatible date instead of changing production pins.
- Incompatible `std`/sysroot -> inspect compiler/environment overrides, use the selected toolchain's `cargo miri clean`, then repeat setup.
- Unsupported API/FFI/intrinsic -> isolate the boundary, use an equivalent supported path only when it preserves the unsafe contract, and report lost coverage; disabling isolation does not implement missing APIs.
- Panic, leak, aliasing/model disagreement, timeout or race -> follow the diagnostic reference; preserve the original transcript and default checks rather than suppressing the failure.
