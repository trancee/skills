# Kotlin tests

Reuse module framework/source set/assertions. Test public contract.

## JVM/Android

Existing JUnit/TestNG/Kotest/etc. Narrow filtered task -> full module `test`/`check`. Android behavior -> unit or instrumentation task. Java interop contract requires real Java declaration/caller for JVM names, platform null, mutability, overloads, checked errors.

## KMP

Shared=`commonTest`+`kotlin.test`; platform=`jvmTest/jsTest/iosTest/...`. Run discovered target tasks; one target never proves others.

## Coroutines

Use `kotlinx-coroutines-test` when dependency exists and contract covers delay/dispatcher/flow/concurrency. Supported test scope; inject dispatcher/scope owner; no production global dispatcher.
ASSERT relevant: completion/value; cancellation+cleanup; child failure/supervision; flow emissions/error; virtual timeout; no leaked jobs.
Hang => find unowned job/missing await/blocked dispatcher/swallowed cancellation; never inflate real timeout.

## Compiler/build

Compiler/plugin/toolchain change => production+test compile for every inheriting module/target; published API => binary/API check. Warnings-as-errors: capture diagnostic; suppression only requested policy.

Sources: [Kotlin+JUnit](https://kotlinlang.org/docs/jvm-test-using-junit.html), [KMP tests](https://kotlinlang.org/docs/multiplatform/multiplatform-discover-project.html#integration-with-tests).
