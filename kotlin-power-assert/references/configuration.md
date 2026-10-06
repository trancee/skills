# Functions and source selection

Sources: [Power-assert guide](https://kotlinlang.org/docs/power-assert.html) and [Kotlin 2.4.20 `PowerAssertGradleExtension`](https://github.com/JetBrains/kotlin/blob/v2.4.20/libraries/tools/kotlin-power-assert/src/common/kotlin/org/jetbrains/kotlin/powerassert/gradle/PowerAssertGradleExtension.kt).

## Functions

`functions` is a `SetProperty<String>` of fully-qualified callable paths, defaulting to `kotlin.assert`. Assignment replaces the set, so include `kotlin.assert` when it must remain transformed:

```kotlin
powerAssert {
    functions = listOf(
        "kotlin.assert",
        "kotlin.test.assertTrue",
        "kotlin.test.assertEquals",
        "com.example.assertThat",
    )
}
```

Use exact declaration casing/package. Do not include parentheses or parameter types. Verify overload behavior with a deliberate failure. Annotated `@PowerAssert` functions are discovered without this list.

Transformable functions accept the Boolean condition and a final `String` or `() -> String` message shape supported by the compiler plugin. A configured name alone does not prove every overload transforms.

## Source-set and compilation selection

Kotlin 2.4.20: `compilationFilter` is a `Property<PowerAssertCompilationFilter>` over `KotlinCompilation` objects; default = test compilations.

```kotlin
powerAssert {
    compilationFilter.set(PowerAssertCompilationFilter.TESTS)
}
```

Predefined filters:
- `PowerAssertCompilationFilter.TESTS` (default): test compilations.
- `PowerAssertCompilationFilter.ALL`: every compilation, including production.

Custom predicate: compilation names are `main`/`test` (plus declared custom compilation names), not `commonMain`/`jvmTest` source-set names:
```kotlin
powerAssert {
    compilationFilter.set(PowerAssertCompilationFilter { compilation ->
        compilation.name == "test"
    })
}
```

Selecting `main` instruments production code and adds the runtime there. Deprecated `includedSourceSets` takes precedence only when nonempty; empty/default sets use `compilationFilter`. Remove old selectors when migrating; inspect target/compilation identities and compile every selected target.