# Functions and source selection

Sources: [Power-assert guide](https://kotlinlang.org/docs/power-assert.html), [Kotlin 2.4.10 `PowerAssertGradleExtension`](https://github.com/JetBrains/kotlin/blob/v2.4.10/libraries/tools/kotlin-power-assert/src/common/kotlin/org/jetbrains/kotlin/powerassert/gradle/PowerAssertGradleExtension.kt), and [development-branch extension](https://github.com/JetBrains/kotlin/blob/master/libraries/tools/kotlin-power-assert/src/common/kotlin/org/jetbrains/kotlin/powerassert/gradle/PowerAssertGradleExtension.kt).

## Functions

`functions` is a `SetProperty<String>` of fully-qualified callable paths and defaults to `kotlin.assert`.

```kotlin
powerAssert {
    functions.addAll(
        "kotlin.require",
        "kotlin.check",
        "kotlin.test.assertTrue",
        "com.example.assertThat",
    )
}
```

Use exact declaration casing/package. Do not include parentheses or parameter types. Verify overload behavior with a deliberate failure. Annotated `@PowerAssert` functions are discovered without this list.

Transformable functions accept the Boolean condition and a final `String` or `() -> String` message shape supported by the compiler plugin. A configured name alone does not prove every overload transforms.

## Source-set and compilation selection

Kotlin 2.4.10 exposes `includedSourceSets: SetProperty<String>`. Empty/default means all test source sets:

```kotlin
powerAssert {
    includedSourceSets.addAll("commonTest", "jvmTest")
}
```

Use exact Kotlin source-set names. Adding `main`, `commonMain`, or a platform main source set instruments production code and adds the runtime dependency there by default.

The development branch replaces source-set selection with `compilationFilter` presets/predicates and deprecates `includedSourceSets`. That API is not present in the released Kotlin 2.4.10 plugin. Select configuration from the exact target version's released source/docs; never copy master-branch DSL into a stable build.

When migrating to a version that provides `compilationFilter`, compare affected compilations because one compilation can include several source sets, especially in KMP. Compile every selected target after migration.
