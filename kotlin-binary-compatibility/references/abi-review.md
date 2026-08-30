# ABI diff review

An ABI dump is a declaration inventory, not a semantic-version oracle. Any dump delta can fail golden comparison; classify it before accepting or rejecting it.

## Usually binary-incompatible

Class changes:
- remove/rename/move class or containing class
- remove a former superclass from the inheritance chain
- remove an implemented interface
- reduce visibility
- make a non-final class final
- make a concrete class abstract
- change class/interface/annotation kind

Member changes:
- remove/rename member
- change JVM descriptor, including erased parameter/return/field type
- change field to method or method to field
- reduce visibility
- make a non-final member final
- make a concrete method abstract
- switch instance/static form

Map Kotlin source constructs to JVM/KLib declarations. Properties, default parameters, suspend functions, value classes, top-level declarations, `@JvmName`, overload generation, and compiler changes can produce non-obvious signatures.

## Not proven safe by the dump

The validator does not replace review of:
- source compatibility and overload resolution
- behavioral/semantic compatibility
- inline function bodies and constants copied into consumers
- serialization/wire/storage formats
- reflection names/annotations not represented by the selected dump
- native runtime/toolchain compatibility
- documented contracts and opt-in requirements

## Review protocol

1. Compare the generated/reference dump only after running the authoritative check task.
2. Trace every removed/changed signature to source and publication target.
3. Determine consumer linkage behavior, not only source intent.
4. Separate compatible additions from removals/changes; additions still expand supported API.
5. Prefer deprecation bridges and staged removal when release policy requires compatibility.
6. Approve versioning/migration consequences before running update/dump.
7. Inspect the post-update diff; reject filters or mass churn that obscure the intended change.

`internal @PublishedApi` declarations can be part of binary ABI. JVM-public declarations hidden only by convention remain public unless filtered/annotated under explicit policy.
