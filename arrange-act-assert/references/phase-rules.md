# AAA phase rules

## Arrange

Creates the controlled precondition: SUT/dependencies, inputs, fake behavior, environment/database state, clock/randomness, observer registration, expected literals/spec examples, and cleanup ownership.

A constructor or setup API belongs in Arrange when it establishes the starting condition rather than exercising the named behavior. Setup helpers should not hide the focal behavior or assert the outcome.

## Act

Triggers one logical behavior at the public seam and captures its result. “One” means one causal focus, not dogmatically one source line. A request plus response decoding, an awaited command, or a short user workflow may be one Act when the named contract is that workflow.

Act does not include unrelated follow-up behavior, verification, arbitrary sleeps, or retries that are not part of the product contract.

## Assert

Observes consequences: return/response, error, state, event, persistence, UI semantics, or contractually required interaction. Several assertions are appropriate when they form one atomic/coherent outcome. Assertions should use an independent oracle and fail with useful differences.

## Teardown

Cleanup is test infrastructure outside the behavior narrative. Register it during Arrange and guarantee it with framework fixtures/hooks/finally. Never place essential cleanup after an assertion where failure skips it.

## Given-When-Then

Given maps to Arrange, When to Act, Then to Assert. Use domain terms and multiple Given/Then clauses as needed; keep one focal When unless scenario history is the behavior.
