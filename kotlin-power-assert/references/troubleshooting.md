# Diagnostics and migration

## Missing diagram

1. Confirm the caller's module applies the plugin.
2. Confirm compiler/plugin/runtime versions match.
3. Map the call site to its Kotlin source set and the target version's selector (`includedSourceSets` in 2.4.10; version-gated compilation filter later).
4. Confirm exact fully-qualified callable name or `@PowerAssert` metadata.
5. Confirm supported Boolean/message parameter shape.
6. Move causal subexpressions into the transformed call; a precomputed Boolean can expose only its final value.
7. Deliberately fail the narrow path and inspect the thrown message/test report.

## Semantic traps

- JVM `kotlin.assert` throws only with `-ea`; Kotlin/Native assertions also depend on compilation/runtime assertion settings. Use `require`/`check` for unconditional enforcement.
- Short-circuited expressions are not evaluated and cannot have captured values.
- Getters, `toString()`, and custom renderers may throw or produce unstable output; keep assertions side-effect-free.
- Source/offset renderers must handle multiline text, null arguments, ignored/default parameters, Unicode, and changing Experimental expression models.
- Sensitive values can appear in failure output. Mark owned parameters/types ignored or avoid asserting secrets directly.

## Migration

Power-assert is Experimental since Kotlin 2.0.0. For each Kotlin upgrade:

1. read release/migration notes and current runtime/Gradle source
2. align all plugin/runtime artifacts
3. keep `includedSourceSets` on Kotlin 2.4.10; migrate to `compilationFilter` only when the destination release provides it
4. compile every transformed JVM/JS/Native/Wasm/Android compilation
5. verify representative default/custom/annotated calls and renderers
6. verify published library consumers

Treat snapshot text diagrams as brittle unless exact formatting is the observable API. Prefer assertions that required source fragments and values are present.
