# Source synthesis

Supplied sources:
- [Automation Panda](https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/) (2020): phase definitions, Given-When-Then equivalence, one focused behavior, avoid Act-Assert-Act-Assert.
- [Paulo Gomes](https://medium.com/@pjbgf/title-testing-code-ocd-and-the-aaa-pattern-df453975ab80) (2017): phase comments are training aids and become clutter when whitespace/names are sufficient.
- [Semaphore](https://semaphore.io/blog/aaa-pattern-test-automation) (updated 2025): language/framework independence, setup fixtures, concise Act, coherent assertion guidance, automation readability.
- [Jeremy Leyvraz](https://medium.com/@jeremy.leyvraz/understanding-aaa-pattern-arrange-act-assert-with-a-kotlin-example-e08755b46b06) (2023): Kotlin example plus drawbacks—large Arrange, duplication, implementation-focused setup, and cases where AAA is not natural.

Synthesis corrections:
- AAA is a readability/causal-structure pattern, not proof that a test is isolated, deterministic, valuable, or behavior-focused.
- One Act means one logical behavior, not always one line.
- One assertion is not mandatory; use one coherent outcome cluster.
- Phase comments are optional.
- Teardown is guaranteed infrastructure outside the three behavioral phases.
- Property/model/fuzz/benchmark/approval and genuine workflow tests may have clearer native structures.
