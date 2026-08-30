# State, recomposition, and effects

Use immutable UI state plus event callbacks. Hoist state to the lowest owner shared by all readers/writers; keep business truth outside composables.

State lifetimes:
- plain parameter: owner-controlled
- `remember`: survives recomposition while call remains in composition
- `rememberSaveable`: survives supported recreation with saveable value/Saver
- ViewModel: screen/graph state and asynchronous work
- repository/use case: durable/domain state

Read observable values through Compose-aware adapters (`collectAsStateWithLifecycle` where appropriate). Avoid copying one mutable source into another unless synchronization ownership is explicit.

Effects:
- `LaunchedEffect(keys)`: suspend work tied to composition/key lifetime
- `DisposableEffect(keys)`: register plus mandatory unregister/dispose
- `SideEffect`: publish successful composition state outward
- `produceState`: bridge callback/suspend source into State
- `rememberCoroutineScope`: launch from user events; cancelled with owner
- `rememberUpdatedState`: observe latest callback/value without restarting a long-lived effect

Effect keys are semantic identities. Missing keys retain stale dependencies; over-broad keys restart work and duplicate requests/listeners. I/O, timers, subscriptions, analytics, navigation, and mutable state writes do not run directly during composition.

Use `derivedStateOf` only when input changes more often than the derived UI should invalidate. Keep lazy-list keys stable and unique. Treat stability annotations/config as contracts; do not mark mutable/unstable types stable to silence recomposition.

Diagnose with observable duplicate work, recomposition tracing/compiler reports, state-owner inspection, and the narrowest screen reproduction. Optimization follows measurement, never guesswork.
