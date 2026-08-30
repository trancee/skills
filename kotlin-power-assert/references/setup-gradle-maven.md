# Gradle and Maven setup

Sources: [Power-assert guide](https://kotlinlang.org/docs/power-assert.html) and [Kotlin 2.4.10 Gradle plugin source](https://github.com/JetBrains/kotlin/blob/v2.4.10/libraries/tools/kotlin-power-assert/build.gradle.kts).

## Gradle

Use the same version owner as the Kotlin plugin:

```kotlin
plugins {
    kotlin("jvm") version kotlinVersion
    kotlin("plugin.power-assert") version kotlinVersion
}
```

Full ID: `org.jetbrains.kotlin.plugin.power-assert`. In a convention-managed build, declare/apply without duplicating the version.

The plugin adds `kotlin-power-assert-runtime` as an implementation dependency to transformed compilations by default. `addRuntimeDependency.set(false)` transfers responsibility for the matching runtime dependency to the build.

The Gradle extension is Experimental Kotlin Gradle Plugin API. Scope `@OptIn(ExperimentalKotlinGradlePluginApi::class)` to the configuration that uses it.

## Maven

Inside `kotlin-maven-plugin`:

```xml
<configuration>
  <compilerPlugins>
    <plugin>power-assert</plugin>
  </compilerPlugins>
  <pluginOptions>
    <option>power-assert:function=kotlin.assert</option>
    <option>power-assert:function=kotlin.test.assertTrue</option>
  </pluginOptions>
</configuration>
<dependencies>
  <dependency>
    <groupId>org.jetbrains.kotlin</groupId>
    <artifactId>kotlin-maven-power-assert</artifactId>
    <version>${kotlin.version}</version>
  </dependency>
</dependencies>
```

Keep `kotlin-maven-plugin`, `kotlin-maven-power-assert`, compiler, and runtime on one Kotlin version. Preserve existing compile/test-compile executions. Library authors add `org.jetbrains.kotlin:kotlin-power-assert-runtime` explicitly where needed.
