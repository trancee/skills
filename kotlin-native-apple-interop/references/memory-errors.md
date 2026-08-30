# ARC/GC, callbacks, and errors

Source: [Swift/Objective-C ARC integration](https://kotlinlang.org/docs/native-arc-integration.html).

Kotlin uses tracing GC; Swift/Objective-C uses ARC. Crossing objects can outlive the Swift lexical scope until Kotlin GC. Deinitializers commonly run on Main when objects entered Kotlin on Main and its queue is processed; otherwise they can run on a special GC thread. Never rely on immediate deinit or one fixed thread without an explicit contract.

Long Kotlin loops producing temporary Objective-C objects can grow autoreleased/stable roots. Measure GC logs/stable refs and wrap iteration bodies with `autoreleasepool` when appropriate.

Mixed retain cycles containing Objective-C objects cannot be reclaimed as a whole. Break Swift/Objective-C strong cycles using weak/unowned ownership. No automatic cross-runtime cycle detector exists.

## Callbacks

Define callback owner, registration/unregistration, invocation thread, multiplicity, and post-cancel behavior. Function types map through Objective-C blocks; primitive parameters can box and Unit returns map to KotlinUnit. `StableRef` lifetime must span native callback registration and end exactly once.

## Exceptions

Objective-C exceptions crash by default when entering Kotlin; `foreignExceptionMode=objc-wrap` converts them to `ForeignException`, but this changes boundary semantics and must be tested.

Kotlin -> Apple:
- non-suspend `@Throws(E::class)` maps listed classes/subclasses to NSError/Swift throws
- unlisted escaping exception terminates
- suspend completion always has an error channel; without `@Throws`, only cancellation is propagated
- Swift throwing APIs are not imported to Kotlin as Kotlin-throwing functions automatically

Completion handlers for exported suspend functions can run off Main. Dispatch UI updates explicitly and test cancellation/thread behavior.
