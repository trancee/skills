# Multiplatform testing

Source: [Test your multiplatform app](https://kotlinlang.org/docs/multiplatform/multiplatform-run-tests.html).

## Placement

- common contract: `commonTest`, `kotlin.test`
- intermediate contract: matching intermediate test set
- JVM-specific: `jvmTest`, JUnit/TestNG as configured
- Android host: `androidHostTest`; device tests require explicit builder/configuration
- JS/Wasm: target environment test task (browser or Node)
- Native: target test executable on capable host

A common test is compiled and executed through target-specific runners. One target pass does not cover other actual implementations/runtimes.

## Task strategy

List tasks and run narrow `<targetName>Test`/environment task first. Run aggregate `allTests` only when the host supports its enabled targets. Disabled/skipped native tasks are gaps, not passes.

Test:
- pure shared logic on at least representative targets
- every expect/actual implementation
- platform-specific dependencies/integrations
- serialization/coroutine/threading/filesystem/locale behavior per runtime
- publication consumer compilation when API metadata changes

Keep fixtures in the highest source set whose APIs they use. Do not add JVM test frameworks to commonTest.

## Host matrix

Linux: JVM/JS/Wasm/Linux Native; no Apple final binaries/tests. macOS: Apple targets/Xcode plus others. Windows: JVM/JS/Wasm/mingw; host rules vary. Use live native target support.

Record task, target, host, runner, result, and skipped reason. CI should partition target tasks across capable hosts rather than silently suppress disabled targets.
