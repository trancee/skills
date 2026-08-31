# Async, integration, UI, and event tests

Async:
- Arrange scheduler/dispatcher/clock and observers.
- Act starts/awaits one command.
- Assert advances virtual time or awaits bounded condition and verifies outcome.
- Teardown cancels children/resources even on failure.

Integration/API:
- Arrange isolated database namespace, server fixture, user/credentials, and expected response from contract.
- Act sends one request/message/transaction.
- Assert response plus coherent persisted/emitted effects through declared seams.
- Cleanup via transaction rollback or unique-resource deletion in guaranteed teardown.

UI:
- Arrange rendered state/dependencies/navigation host.
- Act performs one user intent (tap/type/submit/gesture).
- Assert accessibility semantics, visible state, navigation, or external effect after idleness.
- Avoid multiple journeys in one test unless the journey is the named end-to-end behavior.

Events/jobs:
- Arrange subscription/probe before trigger to avoid missed events.
- Act publishes/executes once.
- Assert exact events/order/content and absence only within a bounded deterministic window.

Exceptions:
`assertThrows`, `assertFailsWith`, `pytest.raises`, and similar constructs combine invocation and exception capture. Treat the block as Act and the helper’s type check as the first Assert; put stable error-field assertions afterward.
