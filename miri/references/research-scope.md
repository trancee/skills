# Research claims and validation boundaries

## Interpret the supplied paper page

The [ETH research page](https://plf.inf.ethz.ch/research/popl26-miri.html) introduces *Miri: Practical Undefined Behavior Detection for Rust*, Ralf Jung et al., POPL 2026, [DOI 10.1145/3776690](https://doi.org/10.1145/3776690). Its abstract claims the first tool able to find **all de-facto UB in deterministic Rust programs** and reports successful execution of more than 70% of tests across over 100,000 libraries.

1. Preserve **deterministic**, **de-facto**, the supported execution boundary, and the tool/model version when restating that claim. It describes the detector's intended breadth, not a promise that a selected passing test suite proves an entire library sound.
2. Separate the empirical corpus result from a theorem: 70% test execution is not 70% soundness, proof coverage, or permission to classify the remaining tests as UB. Unsupported operations and setup failures are distinct outcomes.
3. Use the [pinned upstream limitations](https://github.com/rust-lang/miri/blob/89224698f215583aef7e10554598cd0f5445a455/README.md) to bound current operational claims. Miri implements an approximation of Rust UB; Rust's exact unsafe semantics, especially aliasing, are not fully settled. Tool bugs and future compiler changes remain possible.
4. Record that the full ACM PDF was inaccessible during this skill's source inspection (HTTP 403). The page/abstract and artifact metadata were inspected; no full-paper completeness theorem or experimental methodology was independently audited.

## What a run establishes

Miri interprets Rust MIR while tracking allocation bounds/lifetime, initialization, type validity, alignment, pointer provenance, reference aliasing and concurrent memory accesses. It detects UB in executed code, including unsafe dependencies reached by otherwise safe tests. It additionally reports leaks, which alone are not Rust UB.

- A concrete UB diagnostic is evidence of an invalid execution under the recorded model; inspect the violated precondition and allow for a minimized tool/model bug report when justified.
- Soundness requires that **every** safe client interaction uphold the unsafe implementation's contract. Finite inputs, selected features, one seed, or even many seeds cannot establish that universal property.
- Addresses, schedules and some weak-memory behaviors vary by seed. Weak-memory emulation is incomplete; some legal behaviors are never produced. A passing deterministic replay does not enumerate all possible executions.
- Unspecified layout, target-specific branches and unsupported native/OS operations limit coverage. An interpreter error saying `unsupported operation` is neither a UB counterexample nor successful validation of that path.
- Stacked Borrows is the pinned baseline's default aliasing model; Tree Borrows is an experimental alternative. Compare results as model-specific evidence, not a final language ruling. Neither a more permissive model nor disabled checks repairs an observed ownership violation.
- Miri's deterministic host isolation is **not a security sandbox**. Cargo build-time code runs outside that interpreter isolation; fake RNG output must not be used to generate cryptographic keys.

Use the [Rust Reference's UB list](https://doc.rust-lang.org/reference/behavior-considered-undefined.html) and [soundness definition](https://rust-lang.github.io/unsafe-code-guidelines/glossary.html#soundness-of-code--of-a-library) for the language/contract distinction. Consult the operational references for flags and unsupported-boundary handling instead of inferring tool support from the paper title.

## Reproduce the artifact, not an imagined current equivalent

The [Zenodo artifact](https://zenodo.org/records/17334726), DOI **10.5281/zenodo.17334726**, is version 1, published 2025-10-12. Its source artifact is pinned to **nightly-2025-10-10**; it includes instructions for the paper's features and Figure 9 benchmark plus retained logs for the Figure 7 crates.io evaluation.

1. Select the artifact only when reproducing that research snapshot. Read its own instructions, toolchain and dependency requirements; a current `rustup` Miri component is not byte-for-byte the paper artifact.
2. Distinguish qualitative reproduction of performance trends from exact timing on different hardware. The live crates.io experiment cannot be replayed exactly from a future registry state; retained logs are evidence of the original evaluation, not freshly executed tests.
3. Bound resource requirements before downloading: the record lists a roughly 2.9 MB source archive and 233 MB compressed logs expanding to about 43 GB. Large logs/corpus evaluation were not downloaded or rerun while authoring this skill.
4. For ordinary consumer diagnosis, use the recorded current nightly/component and the upstream documentation matching it. This skill's usage reference is pinned to Miri source **89224698f215583aef7e10554598cd0f5445a455** (2026-10-23); the exercised rustup component is recorded separately in run evidence.