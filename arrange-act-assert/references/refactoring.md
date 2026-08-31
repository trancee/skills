# Refactoring tests into AAA

Inventory each test:
- name and intended behavior
- public seam
- fixture/setup and hidden shared state
- focal and secondary actions
- assertions/oracles
- cleanup
- current pass/fail and sensitivity evidence

Safe sequence:
1. add whitespace/temporary phase labels without moving code
2. classify ambiguous calls by causal role
3. move prerequisite setup before focal action
4. move observations/assertions after action without changing oracle
5. guarantee cleanup independently
6. run test
7. split unrelated Act-Assert cycles; reconstruct each precondition independently
8. extract phase-specific helpers and remove temporary comments if redundant
9. run owning suite and mutation/known-defect check

Do not mechanically split when the contract is an ordered workflow, state-machine trace, protocol transcript, or end-to-end journey. In those cases use explicit scenario steps/Given-When-Then/model commands and retain a clear final oracle.

Common hidden acts: fixture builders that call the tested API, lazy properties that perform I/O, mocks whose setup invokes callbacks, “get result” helpers that mutate, and assertion helpers that refresh/retry the system. Make these causal operations visible.

Shared `beforeEach`/fixtures can arrange universal cheap isolation. Keep behavior-specific values in the test. Avoid `beforeAll` mutable state that couples order or parallel execution.
