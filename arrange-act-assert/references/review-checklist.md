# AAA review checklist

- [ ] Test name states behavior, condition, expected result.
- [ ] Public seam and independent oracle are identifiable.
- [ ] Arrange contains only necessary deterministic preconditions and observer/cleanup registration.
- [ ] Scenario-critical inputs remain visible.
- [ ] Act has one logical causal focus and captures the result.
- [ ] Assert follows Act and contains one coherent outcome cluster.
- [ ] Each assertion can fail for a plausible defect and avoids implementation details.
- [ ] Async/UI/event synchronization uses clock/idleness/signal/bounded eventual checks, not sleep.
- [ ] Cleanup runs when Arrange/Act/Assert fails and supports parallel execution.
- [ ] Helpers belong to one named phase and do not hide the test story.
- [ ] Parameterized cases each execute independently.
- [ ] Comments add information; redundant Arrange/Act/Assert markers are absent unless conventional/teaching.
- [ ] Exceptions to AAA use a clearer named structure (property/model/BDD/workflow/benchmark).
- [ ] Narrow test and owning suite pass; mutation/known defect proves sensitivity.
