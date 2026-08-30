# Lifecycle, ViewModel, and navigation

Sources: [lifecycle](https://kotlinlang.org/docs/multiplatform/compose-lifecycle.html), [ViewModel](https://kotlinlang.org/docs/multiplatform/compose-viewmodel.html), and [navigation](https://kotlinlang.org/docs/multiplatform/compose-navigation.html).

Use compatible `org.jetbrains.androidx.lifecycle` and `org.jetbrains.androidx.navigation` artifacts in `commonMain`. Their versions are independent component versions; select them from the Compose release table/current docs.

Common lifecycle maps native events but differs by platform: web skips `CREATED` and normally never reaches `DESTROYED`; desktop maps focus/iconify/dispose; iOS maps controller/app notifications. Code against required state semantics rather than assuming Android callbacks.

Lifecycle/ViewModel scopes use `Dispatchers.Main.immediate`; desktop commonly needs `kotlinx-coroutines-swing`. Common `viewModel()` construction must pass an initializer/factory because non-JVM targets cannot reflectively instantiate the class.

Keep ViewModel UI state immutable and expose flows; inject platform services through interfaces. Tie ViewModel ownership to the screen/navigation entry that owns the state. Navigation 3 requires explicit saveable-state/ViewModel entry decorators where documented.

Use serializable typed routes. Route arguments are stable IDs/minimum values, not repositories, files, images, application state, or ViewModels. Load current data at the destination from its source of truth.

Define one navigation graph owner and test start destination, push/pop/up, nested/multiple back stacks, restoration, deep links, and empty-stack behavior. Register external deep-link schemes per platform. Default back mappings differ: Android gesture/button, iOS gesture behavior/configuration, desktop Esc; custom transitions can replace platform defaults.
