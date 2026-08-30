# Kotlin compiler options

Source: [compiler options in KGP](https://kotlinlang.org/docs/gradle-compiler-options.html).

## Precedence

1. Kotlin extension `compilerOptions`: defaults for all targets/shared source sets
2. target `compilerOptions`: overrides extension for that target
3. compilation/task `compilerOptions`: narrowest override

Prefer the highest level that expresses policy once. Inspect task-level overrides before assuming extension options apply.

```kotlin
kotlin {
    compilerOptions {
        allWarningsAsErrors.set(true)
        progressiveMode.set(true)
        optIn.add("com.example.ExperimentalApi")
        languageVersion.set(org.jetbrains.kotlin.gradle.dsl.KotlinVersion.KOTLIN_2_4)
    }
}
```

## Migration

`kotlinOptions {}` is deprecated since Kotlin 2.0. Move `android.kotlinOptions` to `kotlin.compilerOptions` or target compiler options.

- strings -> typed values such as `JvmTarget.JVM_21`, `KotlinVersion.KOTLIN_2_4`, `JvmDefaultMode`
- `freeCompilerArgs +=` -> `add`/`addAll`
- `-opt-in` -> `optIn`
- `-progressive` -> `progressiveMode`
- `-Xjvm-default=all-compatibility` -> `jvmDefault=ENABLE`
- `-Xjvm-default=all` -> `jvmDefault=NO_COMPATIBILITY`
- `-Xjvm-default=disable` -> `jvmDefault=DISABLE`

Use `freeCompilerArgs` only when no typed DSL exists. Experimental `-X` flags can change without compatibility.

## Verification

Run the exact compile task with `--debug`; find `Kotlin compiler args:` for JVM/JS/Wasm or `Arguments =` for Native. Do not retain debug logs containing secrets. Check task names through `tasks --all`: JVM main/test default to `compileKotlin`/`compileTestKotlin`; custom/Android/KMP names derive from compilation/variant.
