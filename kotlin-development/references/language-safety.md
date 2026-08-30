# Kotlin safety/interop

## Null

Absence stays nullable until handled. Prefer smart cast, `?.`, `?:`, `requireNotNull`, explicit boundary error. `!!` only local proven invariant + programmer-error violation. Never map absence to empty/zero unless contract. Details: [null safety](https://kotlinlang.org/docs/null-safety.html).

## Java

Unannotated Java reference=>platform type; runtime null can fail assignment/call. At boundary: explicit Kotlin type OR correct owned-Java nullability annotation.
Check as relevant: getter/setter properties; collection mutability; `void`=>`Unit`; keyword backticks; SAM; checked exceptions; wildcards; defaults; generated JVM names.
READ [Java from Kotlin](https://kotlinlang.org/docs/java-interop.html)+[Kotlin from Java](https://kotlinlang.org/docs/java-to-kotlin-interop.html) before cross-language public API change.

## Coroutines

High-level `launch`/`async`/`flow` belong to separate `kotlinx.coroutines` dep.
- owned structured scope (app/request/lifecycle/test); ordinary work not `GlobalScope`
- `coroutineScope`: child failure cancels siblings
- `supervisorScope`: siblings intentionally independent + each error path
- cancellation cooperative; CPU loop uses `yield`/`ensureActive`; caught `CancellationException` rethrown after cleanup
- `launch`: completion; `async`: concurrent value consumed by `await`; no orphan `Deferred`
READ [guide](https://kotlinlang.org/docs/coroutines-guide.html), [cancellation](https://kotlinlang.org/docs/coroutines-cancellation.html), [exceptions](https://kotlinlang.org/docs/exception-handling.html) before scope/failure change.

## API/style

Published declaration: explicit type if inference may alter ABI/JVM signature. Check defaults, inline, sealed, value class, variance, nullability.
Style precedence: repo formatter/static rules > [Kotlin conventions](https://kotlinlang.org/docs/coding-conventions.html). Default: 4 spaces; lowercase package; UpperCamel type; lowerCamel function/property; related declarations together; no generic utility bucket.
