# Verification, validation, and progress

Sources: [Results verification](https://kotlinlang.org/docs/lincheck-results-validation.html) and [Progress guarantees](https://kotlinlang.org/docs/lincheck-progress-guarantees.html).

## Sequential specification

Lincheck seeks a sequential ordering that yields the observed results. By default it uses the tested operations themselves. Supply `sequentialSpecification(Reference::class.java)` when a simpler trusted implementation defines correct sequential behavior. Operation names/signatures/results must correspond.

## Verifiers

- `LinearizabilityVerifier` default: preserves real-time happens-before between nonoverlapping operations
- `SerializabilityVerifier`: some sequential order may explain results, ignoring real-time order
- `QuiescentConsistencyVerifier`: relaxes ordering around operations marked quiescent-consistent

A weaker verifier can make an invalid contract pass. Select only when the public semantics allow it.

## Final-state validation

Annotate argument-free functions with `@Validate`; throw when the invariant fails. Use for representation constraints not observable from operation return values: size accounting, links, uniqueness, conservation. Validation complements, not replaces, operation-result verification.

## Progress

`checkObstructionFreedom()` checks whether one thread can progress while others pause. Lincheck does not verify lock-freedom or wait-freedom directly. Because those imply obstruction freedom, an obstruction-freedom failure disproves the stronger claim; a pass does not prove it.

Mark an operation `blocking=true` only if blocking is intentional contract behavior. Otherwise the flag can hide a progress bug. Model checking loop/stall detection and 3.7 await-path detection help identify spin loops; confirm side effects and bounds before classification.
