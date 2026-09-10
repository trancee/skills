# Status, constructions, parameters, and evidence

## Scope map

| Construction/material | Role | Skill treatment |
| --- | --- | --- |
| CSIDH | Commutative supersingular-isogeny class-group action and NIKE proposal | In scope; pin paper/source/parameters |
| CTIDH | Constant-time-oriented CSIDH-family action with its own key space/algorithm | In scope; not wire/API interchangeable with CSIDH |
| dCSIDH/dCTIDH | Later dummy-free/high-security research variants | In scope only at exact pinned revision |
| VeluSqrt | Faster large-prime-degree isogeny computation | Optimization primitive, not protocol/parameter security proof |
| Quantum evaluation | Attack-cost methodology/code for isogenies | Parameter-evidence input, not implementation certification |
| `sina1777/CSIDH` `SW/` | Modified C model for FPGA/ASIC testbench comparison | Pinned research/hardware co-verification artifact; not canonical or production reference |
| SIDH/SIKE | Torsion-point key exchange/KEM family | Out of scope and cryptographically broken |
| SQISign/isogeny signatures | Signature constructions | Out of scope |

CSIDH-family schemes are research proposals, not NIST/IETF standards. Never translate a paper's target level, key size, or constant-time claim into certification or broad production approval.

## Construction identity

A complete identity includes:

- Construction and revision: CSIDH, CTIDH, dCSIDH, dCTIDH, or named fork.
- Paper/specification citation and version/date.
- Source repository/archive and immutable commit/digest.
- Prime `p`, its bit length, small-prime list/factorization structure, curve model, base curve.
- Secret-exponent distribution/bounds and encoding.
- Public-key encoding and full validation algorithm.
- Class-action algorithm/schedule and enabled optimizations.
- Claimed attack costs and model/date.

A label such as `CSIDH-512`, `CTIDH-512`, or `2047` is insufficient by itself. Projects have used nearby sizes with different parameter lists, bounds, algorithms, and security assumptions.

## Historical baselines

Original CSIDH proposed a roughly 512-bit prime and compact public keys (a Montgomery coefficient, commonly 64 bytes for that set). It was a research proof of concept. Quantum/classical attack estimates and the interpretation of “128-bit” security have evolved; do not use the original label without current analysis.

The historical CTIDH software archive dated 2021-05-23 provides research implementations around 511/512/1024/2048-bit sizes. Its documented build targets require ADX-capable x86-64 processors (for example Broadwell/Zen or newer) and a Linux/clang/Valgrind-oriented test environment. Confirm current source and hardware rather than copying this tuple.

High-security CSIDH research published in 2023 evaluated much larger primes (roughly 2048 through 9216 bits depending on security level and attack assumptions) and reported handshake latency in the tens-of-seconds regime for conservative sets. Its `kemtls-secsidh/code` repository is archived. Treat the study as dated parameter evidence, not a maintained implementation recommendation.

Later dCTIDH auxiliary implementations include 2047-bit research parameter sets and their own compiler/ADX/test assumptions. Pin exact paper and repository commit; active development alone is not production maintenance.

## Hardware golden-model artifact

At `sina1777/CSIDH@770d2a198e109f30014af87ae38502f03c61203a`, `SW/` is a modified C model adapted from the original CSIDH software for comparison with the repository's Verilog FPGA/ASIC accelerator (arXiv:2508.11082). It contains `p512` and `p1024` variants whose actual field sizes are 511 and 1020 bits, with distinct prime lists and exponent bounds.

Use it only when reproducing or reviewing that hardware project. Pin the commit and parameter directory, rebuild from source, and compare hardware outputs against independently verified vectors/baselines. Do not infer current high-security parameters from its `512`/`1024` labels.

The repository commits built `SW/libcsidh.so` and `SW/main`; do not trust or redistribute these binaries. No repository-level license file or license text was found at the inspected commit; the README attributes the model to modified public-domain original code and points to the original license. Resolve provenance and licensing for every copied file before reuse.

## Security estimate record

For every claimed level, record:

- Best known classical attack and cost metric.
- Best known quantum attack/oracle model.
- Quantum queries, depth, gates/time, memory/qubits, and parallelism assumptions.
- Cost assigned to one class-group action/isogeny oracle.
- Precomputation/multi-target assumptions.
- Parameter validation and malformed-key attack assumptions.
- Source/date and uncertainty range.

The quantum evaluation material at `quantum.isogeny.org` helps translate attacks into resource estimates. Do not cite only an exponent without its cost model.

## Performance record

Measure rather than inherit paper numbers:

- Key generation/public action.
- Public-key validation.
- Shared secret action.
- Canonical encoding/decoding and KDF.
- Complete protocol handshake and confirmation.
- Median, high percentile, worst observed, memory/stack, code size, and energy where relevant.
- Valid and adversarial invalid-key paths.

Large conservative parameters can make the construction operationally unsuitable even when key sizes remain attractive.

## Source refresh

Before selection:

1. Read `https://isogeny.org/` and linked construction pages.
2. Pin the exact paper and implementation commit/archive.
3. Search current cryptanalysis and implementation/fault literature.
4. Check repository archive/maintenance/security-response status.
5. Reproduce tests and benchmarks on the target.
6. Record all unverified security assumptions.
7. For hardware co-verification, inspect pinned `https://github.com/sina1777/CSIDH/tree/main/SW` as a modified golden model, not the canonical CSIDH implementation.
