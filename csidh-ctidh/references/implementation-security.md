# Implementation, constant-time, optimization, and fault security

## Implementation threshold

Prefer a pinned, reviewed implementation matching the exact construction and parameter set. From-scratch work requires ownership of:

- Finite-field arithmetic and canonical encoding.
- Montgomery/supersingular curve operations.
- Isogeny evaluation and kernel-point handling.
- Class-group action algorithm and exponent schedule.
- Full public-key validation.
- Constant-time and fault analysis.
- Parameter-generation evidence.
- Target assembly/compiler dispatch and long-term maintenance.

The original CSIDH implementation is proof-of-concept evidence. Historical CTIDH and later dCTIDH repositories are research implementations with specific hardware/toolchain assumptions; re-evaluate, do not inherit suitability.

## sina1777 hardware golden model

At commit `770d2a198e109f30014af87ae38502f03c61203a`, `sina1777/CSIDH/SW` is useful only as the modified C golden model for that repository's RTL co-verification.

Before any use:

1. Rebuild `p512` or `p1024` from source; ignore committed `libcsidh.so` and `main` binaries.
2. Resolve license/provenance for the exact copied files; the inspected repository has no root license text.
3. Remove or gate extensive `printf` diagnostics, hard-coded private exponent vectors, and private-key printing before secret-bearing tests.
4. Treat the source as variable-time: inspected `SW/csidh.c` states it is “totally not constant-time” and branches on secret exponent/real-dummy decisions despite broader repository claims.
5. Replace `-march=native -O3 -DNDEBUG` with an explicit reproducible target configuration and retain assertions/checks required by verification.
6. Replace RNG helpers that exit the process on `/dev/urandom` failure with a caller-visible fail-closed interface for integration.
7. Independently verify public-key validation, parameters, and vectors against the original construction/paper; `csidh()` couples validation and action rather than enforcing a typed validated-key boundary.
8. Run software CT/fault tests and RTL simulation/synthesis/hardware side-channel tests separately. Golden-output agreement proves functional matching only.

## Constant-time inventory

Inspect secret influence on:

- Exponent digit/sign and remaining-count decisions.
- Choice of real versus dummy isogeny.
- Prime/isogeny order and loop counts.
- Kernel-point search and rejection.
- Field/curve exceptional cases.
- Table and array indices.
- Conditional swaps/moves.
- Random sampling retries.
- Error, logging, and cleanup paths.

Use constant-time field primitives, branchless conditional operations, fixed public schedules, or the exact selected algorithm's proven strategy. “Always perform an isogeny” is not enough when real/dummy behavior is distinguishable through faults, memory, or data flow.

## Target evidence

Pin:

- Compiler/version and complete optimization/LTO flags.
- CPU architecture/features and runtime dispatch.
- ADX/vector/scalar assembly path.
- Integer multiplication/division/shift timing.
- Allocator, stack limits, OS, RNG, and exception/signal behavior.
- Binary digest.

Run functional and CT tools separately. Historical CTIDH documentation exposes `make timecop` as a separate target; a successful ordinary `make` does not execute it. Valgrind-style secret marking covers only supported instructions/platforms and does not prove power/EM/fault resistance.

## Dummy-operation fault risk

Implementations that balance secret-dependent work with dummy isogenies can be vulnerable when an attacker injects faults and observes whether a real or dummy step affected output/control flow. Review the exact schedule and fault model.

Potential countermeasures require construction-specific evidence:

- Dummy-free or uniform real-operation algorithms.
- Randomized isogeny order/secret representation.
- Redundant computation and consistency validation.
- Infective/fail-closed response without a distinguishing oracle.
- Hardware voltage/clock/glitch sensors and physical controls.
- Limiting attacker access/rate and rotating secrets.

Never add a final recomputation check and assume fault security; analyze coverage, bypass, output oracle, and induced-failure behavior.

## Randomness

Use a failure-reporting CSPRNG/approved DRBG for secret exponent generation, randomized schedules/blinding, validation randomness, and protocol nonces. Validate distribution/bounds exactly; modulo reduction or retry changes can bias exponents.

Test entropy failure, process fork, VM snapshot/clone, concurrent key generation, and deterministic test hooks. Keep test seeds unreachable from production APIs.

## Parameter generation

Custom parameters are a separate cryptographic design task. Record generation script/version/seed, primality and factorization checks, small-prime list, bounds, base curve, validation compatibility, attack estimates, and independent reproduction. Exclude timestamps/random unrecorded state.

Do not alter prime lists/exponent bounds to improve benchmarks while retaining a prior parameter name/security claim.

## VeluSqrt and optimizations

VeluSqrt reduces large-prime-degree isogeny work under specific formulas and preconditions. Before adoption:

1. Pin paper/code revision and exact integrated path.
2. Prove field/curve/kernel/degree preconditions for every call.
3. Compare outputs to the baseline isogeny evaluation.
4. Reassess constant-time memory/control flow and exceptional cases.
5. Reassess fault behavior and intermediate validation.
6. Benchmark end-to-end action, not isolated arithmetic only.

Apply the same discipline to batching, SIMBA-style strategies, vectorization, ADX assembly, projective formulas, and alternate Elligator/kernel generation.

## Diagnostics and secrets

Never log exponent vectors, real/dummy decisions, kernel points, retry counts tied to secrets, action intermediates, or shared pre-key material. Treat timing traces and performance counters as sensitive during analysis. Scrub secrets with an optimization-resistant target primitive where the threat model requires it.
