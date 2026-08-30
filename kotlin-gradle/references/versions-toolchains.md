# Kotlin Gradle versions and toolchains

Sources: [project configuration](https://kotlinlang.org/docs/gradle-configure-project.html) and live [KGP variants](https://kotlinlang.org/docs/gradle-plugin-variants.html).

## Compatibility snapshot

KGP 2.4.0–2.4.10 is fully supported with Gradle 7.6.3–9.5.0 and AGP 8.5.2–9.1.0. Newer Gradle/AGP may resolve but can expose deprecations or unsupported features. Always use the live table for other KGP versions.

Keep version ownership in existing catalog/root settings/convention build. KGP adds matching stdlib automatically unless explicitly disabled/overridden.

## JVM toolchain

```kotlin
kotlin {
    jvmToolchain(21)
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
    }
}
```

A Kotlin toolchain also configures related Java compile/test/Javadoc tasks. It supplies `-jdk-home` and infers `jvmTarget` when unset. The Kotlin compiler process itself runs on the Gradle daemon JDK; compile class libraries/toolchain can differ.

Gradle 8.0.2+ needs a toolchain resolver plugin only when downloading missing JDKs. Preserve the repository's resolver and provision policy.

## Target validation

Related Kotlin/Java tasks must agree. Gradle 8+ defaults Kotlin validation to error. Treat `kotlin.jvm.target.validation.mode=warning|ignore` as weakened validation; fix `jvmTarget`/`targetCompatibility`/toolchain instead.

Without toolchain/explicit alignment, Kotlin can emit JVM 1.8 bytecode while Gradle module metadata declares the daemon JDK requirement. Verify both classfile target and `org.gradle.jvm.version` publication attribute.

## KGP variants

KGP publishes variants for Gradle families. Run with `--info` and inspect `Using Kotlin Gradle plugin <variant> variant`. A custom configuration resolving `kotlin-gradle-plugin` must carry documented plugin API and JVM environment/version attributes; never force the first candidate variant.
