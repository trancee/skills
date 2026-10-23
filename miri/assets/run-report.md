# Miri run record

## Scope
- Package/revision, Cargo lockfile, selected tests/binaries and relevant unsafe contract:
- Host, interpreted target, rustc -Vv, cargo -V, cargo miri --version, exact nightly:
- Full command, Cargo features, MIRIFLAGS, RUSTFLAGS/RUSTDOCFLAGS, isolation/environment exceptions:
- Seed or half-open seed range, aliasing model, layout configuration:

## Result
| Run / target / seed | Exit | Tests actually executed / ignored | Diagnostic / observed behavior |
| --- | ---: | --- | --- |

## Diagnosis and repair
- First failing operation, allocation/free or conflicting accesses and minimal reproducer:
- Classification: UB, experimental aliasing/provenance rule, leak policy, panic/assertion, unsupported operation, isolation denial, build/setup failure, or timeout:
- Violated invariant and source/API requirement:
- Production fix and failing-before/passing-after evidence with the same configuration:
- Native regression result and additional targets/seeds tested:

## Limits
- Unsupported/ignored paths and their separate native/integration coverage:
- Remaining inputs, schedules, target features, layout choices, FFI and external code not checked:
- Changed/disabled checks, if any; no universal soundness or future-compiler guarantee inferred:
