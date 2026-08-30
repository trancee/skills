# Kotlin language safety and interop

## Nullability

Model absence with nullable types. Use smart casts, safe calls, Elvis expressions, `requireNotNull`, or an explicit boundary error according to the contract. Use `!!` only when the code proves the invariant locally and a violation is a programmer error.

Keep nullable values nullable until the code handles the absent case. Avoid replacing a meaningful absence with an empty string, zero, or empty collection unless that value is the contract.

Read [Null safety](https://kotlinlang.org/docs/null-safety.html) when a diagnostic involves smart casts, initialization order, nullable receivers, or Java values.

## Java interop

Java declarations without recognized nullability annotations produce platform types. Kotlin allows a platform value to flow into either a nullable or non-null type, but a runtime `null` can then fail at the assignment or call. Add an explicit Kotlin type at the boundary or add correct Java annotations when the Java API is owned by the project.

Check these boundary behaviors when relevant:

- Java getters and setters appear as Kotlin properties.
- Java collections can expose uncertain mutability.
- `void` returns `Unit` in Kotlin.
- Java keywords used as identifiers require backticks in Kotlin.
- SAM conversion, checked exceptions, wildcards, default arguments, and generated JVM names affect Java callers of Kotlin APIs.

Read [Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html) and [Calling Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html) before changing a cross-language public API.

## Coroutines

Kotlin's standard library provides the low-level coroutine language support. High-level builders such as `launch`, `async`, and `flow` come from `kotlinx.coroutines`, which is a separate dependency.

Keep work in structured scopes owned by the application, request, lifecycle, or test. Avoid `GlobalScope` for ordinary application work. Use `coroutineScope` when one child failure must cancel its siblings. Use `supervisorScope` only when sibling failures are intentionally independent and each child has an error-handling path.

Cancellation is cooperative. Suspending calls check cancellation. CPU loops must call `yield`, `ensureActive`, or another cancellation check. If code catches `CancellationException`, rethrow it after cleanup.

Use `launch` for work whose result is completion. Use `async` when the caller consumes a concurrent result with `await`. An exception held in an unawaited `Deferred` can be missed by the intended error path.

Read the [Coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html), [Cancellation](https://kotlinlang.org/docs/coroutines-cancellation.html), and [Coroutine exception handling](https://kotlinlang.org/docs/exception-handling.html) before changing scope or failure propagation.

## Public APIs and style

Preserve explicit public types when inference could change the ABI or generated JVM signature. Check default parameters, inline declarations, sealed hierarchies, value classes, variance, and nullability before changing a published declaration.

Follow the repository's formatter and static analysis first. Without a repository rule, follow [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html): use four spaces, keep package names lowercase, use upper camel case for types, and use lower camel case for functions and properties. Put related declarations together instead of creating generic utility files.
