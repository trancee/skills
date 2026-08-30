# Kotlin declaration and platform matching

## Signature checklist

Match all of:
- package and module
- class/object/companion/top-level owner
- member versus extension and extension receiver
- callable/property/type name
- type parameters, variance, upper bounds, nullability
- value parameter types/order, vararg, defaults
- return/property type
- `suspend`, `inline`, `operator`, `infix`, `expect`, `actual`, JVM annotations
- opt-in/deprecation annotations
- platform/source-set label

A Dokka page can group many overloads. For example, stdlib `map` groups arrays, primitive arrays, `Iterable`, `Map`, and unsigned arrays; matching only the name produces the wrong contract.

## Extensions

Extension resolution depends on imports and the static receiver type, not runtime type. Member functions outrank extensions. Multiple imported extensions can be shadowed/ambiguous. Verify the call site with compiler/LSP when overload choice matters.

## Multiplatform

- `common`: callable is available to common source where declared
- `jvm`, `js`, `native`, `wasm`: platform-only declaration/actual/overload
- expect/actual: inspect expect contract plus each relevant actual
- typealias actual: platform type can expose additional members not present in common contract

Platform labels apply to individual overloads/members. A class page supporting several platforms does not make every member common.

## Metadata

`Since Kotlin` or library Since states introduction, not current dependency proof. Experimental annotations require the exact opt-in marker and can change. Deprecation includes level (`WARNING`, `ERROR`, `HIDDEN`) and replacement; inspect both source and binary consequences when relevant.

Compiler diagnostics are authoritative for availability in the actual source set. Use a minimal compile probe with exact imports/types when documentation grouping is ambiguous.
