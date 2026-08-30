# SKIE Swift interop

Read live selected feature page; generated Swift interface wins.

## Enums

SKIE wraps Kotlin enum as Swift enum; original Kotlin type becomes `__Type`; exhaustive switch; Swift-style case naming. Convert via `toKotlinEnum()`/`toSwiftEnum()` or casts.
Limits: generated enum cannot implement original Obj-C protocols; generic type arguments remain original Kotlin enum. Migration: case rename, unreachable `default`, built-ins (`values()` -> `allCases`; `name`/`ordinal` preserved).
Source: [Enums](https://skie.touchlab.co/features/enums).

## Sealed

Generated associated-value Swift enum + `onEnum(of:)`; optional overload supported. Hidden/unexported children collapse into `.else`. Generated enum gains `Hashable` only when exposed direct children permit it. Original sealed type remains class/interface.
Source: [Sealed](https://skie.touchlab.co/features/sealed).

## Suspend

Generated real Swift `async`; Swift cancellation -> Kotlin coroutine; Kotlin cancellation -> Swift `CancellationError`; callable off main thread.
Limits:
- generic class member/extension: `try await skie(instance).method()`
- override original generated `__method`; calls from override to other async work lose SKIE cancellation bridge
- Swift chooses execution thread; code relying on main/caller thread must switch explicitly
Source: [Suspend](https://skie.touchlab.co/features/suspend).

## Flow

Mappings: `Flow`, `SharedFlow`, `MutableSharedFlow`, `StateFlow`, `MutableStateFlow` -> typed SKIE Swift `AsyncSequence` classes. Swift task and Kotlin flow cancellation cooperate. Swift cancellation ends `for await` normally; use `withTaskCancellationHandler` if needed.

Limits:
- custom Flow exception reaching Swift can crash
- no ordinary `as`/`is` cast on transformed Flow wrappers; use conversion constructors
- nullable element uses distinct optional wrapper; wrapper families do not inherit
- no `AsyncSequence` -> `Flow`
- custom Flow types unsupported
- automatic conversion absent inside `List<Flow>`, `Map<*,Flow>`, `Flow<Flow>`, and SKIE-generated suspend return types; convert manually
Source: [Flows](https://skie.touchlab.co/features/flows).

## Functions

SKIE wraps global functions/properties out of file namespace; interface extensions gain member syntax; overload names preserve Swift overload behavior. Name collisions can still rename declarations; inspect generated interface. Configure `FunctionInterop.FileScopeConversion`/`LegacyName`.

## Default arguments

Deprecated implementation, disabled by default. Generates Kotlin overloads; no interface methods. `n` default args creates O(2^n) overloads, max default 5 (<=31 extras). External-library enablement disables Kotlin/Native caching. Enable only targeted declarations with `DefaultArgumentInterop` after measuring compile/API cost.
Source: [Default arguments](https://skie.touchlab.co/features/default-arguments).
