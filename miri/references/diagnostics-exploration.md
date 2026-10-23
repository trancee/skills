# Diagnose the first invalid operation

Source: [pinned upstream diagnostics and flags](https://github.com/rust-lang/miri/blob/89224698f215583aef7e10554598cd0f5445a455/README.md#miri--z-flags-and-environment-variables), [Rust UB Reference](https://doc.rust-lang.org/reference/behavior-considered-undefined.html). Flag spelling/defaults follow the installed nightly, not a semver-stable Miri CLI.

## Classify before changing code

| Observation | Meaning / action |
| --- | --- |
| `Undefined Behavior` | Trace the reported operation and violated API/type/memory precondition; preserve input, seed, target and flags |
| Aliasing/provenance violation | Inspect allocation origin, pointer derivation, reference creation/reborrow, invalidation and later use; record experimental aliasing model |
| `memory leaked` | Additional Miri leak policy; leaks alone are not Rust UB, and safe `mem::forget` can trigger it |
| Panic/assertion failure | Investigate the application oracle; not automatically UB |
| `unsupported operation` / unknown foreign function / unsupported intrinsic | Interpreter cannot execute that boundary; not evidence that the program is UB or clean |
| Isolation rejection | Host interaction blocked by the chosen environment; preserve isolation and minimize environmental requirements first |
| Build/dependency error, missing component/sysroot, timeout | No acceptance result for the intended execution |

Miri aborts an interpreter execution at its first UB/unsupported operation. Earlier tests passing does not establish that remaining tests ran. Reproduce the exact failing test directly, then inspect allocation/deallocation notes and both sides of any race, including dependency code.

## Capture actionable traces

Start with existing flags; append diagnostics intentionally rather than overwriting a consumer's policy:

```bash
MIRIFLAGS="-Zmiri-seed=0 -Zmiri-backtrace=full" cargo +nightly-2026-10-23 miri test test_filter
```

- `-Zmiri-backtrace=full` expands Miri's own diagnostic trace; it does not require disabling isolation.
- `-Zmiri-track-alloc-id=123` traces the allocation ID from **this reproducer**; `-Zmiri-track-alloc-accesses` also traces its reads/writes. IDs can change after edits/configuration changes.
- `-Zmiri-track-pointer-tag=456` traces the creation/invalidation of a pointer tag from the aliasing report. Repair the invalidating ownership/reborrow operation, not just the later dereference.
- `-Zmiri-track-weak-memory-loads` helps locate an atomic load returning an older value. Ordinary scheduling variation is not exhaustive weak-memory exploration.
- For Rust panic backtraces under isolation, selectively pass `-Zmiri-env-set=RUST_BACKTRACE=1`. Host environment variables are not automatically visible to interpreted code.

Keep raw diagnostics and the complete invocation. A native run may appear to work despite UB; native success cannot invalidate a Miri counterexample. For a suspected tool/model bug, minimize it and compare a second documented nightly/model without suppressing the original result; report uncertainty with exact versions.

## Repair the violated invariant

1. Use-after-free/out-of-bounds -> restore owner lifetime, allocation bounds and valid pointer arithmetic, including zero-length/one-past cases. Raw pointer existence and dereference validity are different claims.
2. Uninitialized/invalid values -> initialize required bytes before typed reads; maintain enum/bool/reference invariants and `MaybeUninit` initialized-length/drop discipline. Padding is not an ordinary initialized byte payload.
3. Alignment -> preserve the allocation's alignment; use the appropriate unaligned raw operation when the format requires it, without first constructing a misaligned reference.
4. Aliasing -> track which pointer/reference may access which bytes and when. `UnsafeCell` permits specific interior mutation, not arbitrary lifetime/aliasing violations. Casting through integers is not an ownership or provenance repair.
5. Data race -> fix synchronization and ownership at every conflicting access; `volatile` is not synchronization. Review publication, atomic orderings and initialization, not just the line where Miri detected the race.
6. Leak -> repair lost ownership/destruction when accidental. A deliberately accepted leak policy must be recorded separately from UB coverage.

Retain a small consumer-visible regression test that failed before the fix and passes after under the same nightly, features, seed, target and checks. Then rerun the relevant wider suite and native tests; remove temporary tracing and minimization scaffolds.

## Explore additional executions

```bash
MIRIFLAGS="-Zmiri-many-seeds=0..4" cargo +nightly-2026-10-23 miri test test_filter
MIRIFLAGS="-Zmiri-seed=2" cargo +nightly-2026-10-23 miri test test_filter
MIRIFLAGS="-Zmiri-tree-borrows" cargo +nightly-2026-10-23 miri test test_filter
RUSTFLAGS="-Zrandomize-layout" cargo +nightly-2026-10-23 miri test test_filter
```

The seed range is half-open. Many-seeds runs interpreter instances in parallel; bound the range and retain each failing seed. Record all flags: a seed alone does not fix input, features, target, compiler, model, or environmental nondeterminism. Isolation disabled means real host entropy/clocks can destroy replayability.

Default alias checking at the pinned upstream baseline is Stacked Borrows; `-Zmiri-tree-borrows` selects an alternative experimental model. A pass under one model does not erase a rejection under the other or settle Rust's eventual rules. For a strict-provenance contract, separately run `-Zmiri-strict-provenance`; its integer-to-pointer restriction is a stricter policy, not proof that every rejected exposed-provenance program is language UB. Prefer supported pointer provenance APIs where they express the intended operation.

Layout randomization exposes some unspecified-layout dependencies; set `RUSTDOCFLAGS` as well if the same policy must reach doctests. More seeds, models and targets increase evidence, not universal coverage. For subtle atomic algorithms, complement Miri with a separately justified concurrency model such as Loom and review its assumptions.

## Unsupported platform and host access

1. Reduce the unsupported system boundary without changing the unsafe core being checked. A deterministic in-memory backend is useful only if it still exercises the relevant ownership/aliasing/concurrency behavior.
2. Use a narrowly justified `#[cfg_attr(miri, ignore)]` only for genuinely unsupported tests; document why, count the exclusion, and retain native/integration coverage. Never hide a known UB test with `cfg(miri)` or a Miri-only implementation that skips the unsafe algorithm.
3. Pass only required variables using `-Zmiri-env-forward=NAME` or fixed values using `-Zmiri-env-set=NAME=value`; protect secrets from command logs. This does not grant filesystem/network support.
4. Enable `-Zmiri-disable-isolation` only for a reviewed host-access requirement in a disposable environment, with changed reproducibility/security assumptions recorded. It cannot implement unsupported FFI/network APIs. Never generate cryptographic keys from Miri's fake RNG.
5. Experimental native-library support (`-Zmiri-native-lib`) does not check arbitrary C/C++ behavior and loses initialization/provenance tracking on shared memory. Keep it outside ordinary acceptance evidence and document the blind boundary if explicitly required.

Flags disabling validation, aliasing, alignment or race checks are diagnostic experiments, not acceptable repairs. `-Zmiri-ignore-leaks` specifically changes leak/thread-exit policy; record it and keep default leak checking for the ordinary lane. A run with disabled checks cannot certify the checks it bypassed.
