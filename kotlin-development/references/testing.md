# Kotlin test selection

Use the test framework, source set, and assertion style already present in the affected module. Test behavior through the public boundary that owns the contract.

## JVM and Android

Kotlin JVM tests can use JUnit, TestNG, Kotest, or another configured framework. Keep tests in the repository's existing test source root. Mixed Java and Kotlin tests can run in the same module.

Run the narrow test task first. With Gradle and JUnit, filter a class or method through the owning `test` task when the project supports Gradle test filtering. Then run the module's full `test` or `check` task. Use the project's Android unit-test or instrumentation task for Android-specific behavior.

Test Java interop with real Java declarations when generated names, platform types, collection mutability, overloads, or checked exceptions are part of the contract. A Kotlin-only test cannot prove what a Java caller sees.

## Kotlin Multiplatform

Use `kotlin.test` in `commonTest` for contracts that every target shares. Use `jvmTest`, `jsTest`, `iosTest`, or another target test source set for platform behavior and platform libraries.

Run the target-specific test tasks shown by the Gradle project. Shared tests compile into each target test binary, so one passing target does not cover the others.

## Coroutines

Use `kotlinx-coroutines-test` when the module already depends on `kotlinx.coroutines` and the contract involves delays, dispatchers, flows, or concurrent completion. Run suspending tests under the framework's supported test scope. Inject dispatchers or scope owners rather than using production global dispatchers in deterministic tests.

Assert the behaviors that matter:

- completion and returned values;
- cancellation propagation and cleanup;
- child failure propagation or supervision;
- flow emissions and terminal errors;
- timeout behavior with controlled virtual time;
- absence of leaked jobs after the test.

Do not hide a hung coroutine behind a larger real-time timeout. Find the unowned job, missing await, blocked dispatcher, or swallowed cancellation.

## Compiler and build changes

For compiler option, plugin, or toolchain changes, run both production and test compilation. Exercise every module or target that inherits the changed setting. If the repository publishes APIs, run its binary compatibility or API dump check.

For warnings-as-errors changes, capture the diagnostic before fixing it. Do not suppress a warning to make the build green unless the suppression is the requested compatibility policy.

The official [Kotlin and JUnit tutorial](https://kotlinlang.org/docs/jvm-test-using-junit.html) covers mixed JVM projects. The [Multiplatform project structure](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html#integration-with-tests) describes common and target test source sets.
