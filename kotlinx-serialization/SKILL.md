---
name: kotlinx-serialization
description: "Designs, implements, configures, tests, and troubleshoots kotlinx.serialization across JSON and other formats. Use when applying the serialization compiler plugin and runtime, annotating models, configuring Json, writing custom or contextual serializers, modeling polymorphism, evolving wire schemas, supporting multiplatform formats, or diagnosing missing serializers and decoding failures. Don't use for Java Serializable, Android Parcelize, database ORM mapping, reflection-only object mappers, protocol-schema compiler design, or general Kotlin models with no serialization boundary."
compatibility: "Current kotlinx.serialization runtime 1.11.0 is built with Kotlin 2.3.20. The serialization compiler plugin version matches the Kotlin compiler, while runtime/format libraries use independent kotlinx.serialization versions. JSON is stable; bundled non-JSON formats are experimental. Helper requires Python 3.11+."
metadata:
  category: "development"
  source: "https://kotlinlang.org/docs/serialization.html"
  sourceVersion: "kotlinx.serialization 1.11.0@6956af2e6073347c7832c3c5b374fa3b5a345956; Kotlin Help build 1155"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-30T15:10:58+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-30T15:10:58+02:00"
---

# kotlinx.serialization

## Step 1: Establish the wire contract

1. DEFINE setup | model | JSON policy | custom/contextual serializer | polymorphism | schema evolution | alternative format | failure diagnosis.
2. IDENTIFY producer/consumer versions, format, exact payload/schema, Kotlin targets, trust boundary, compatibility direction, model ownership, compiler plugin/Kotlin/runtime versions, and persistence/transport lifetime.
3. READ the current [serialization guide](https://kotlinlang.org/docs/serialization.html), exact format/API pages, and [release notes](https://github.com/Kotlin/kotlinx.serialization/releases/latest) before version or wire-format changes.
4. TREAT serialized names, discriminator values, field numbers, defaults, nullability, requiredness, and custom descriptor shape as public wire schema.
5. ROUTE build-only Kotlin/Gradle work to `kotlin-gradle`; route API lookup to `kotlin-api-reference`.

Completion: format, schema, compatibility directions, trust/privacy constraints, and all participating versions are explicit.

## Step 2: Inspect configuration and serialization sites

RUN from repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

CONFIRM compiler plugin/Kotlin version alignment, runtime format modules/versions/scopes, targets, `@Serializable` models, serial names/defaults/contextual/polymorphic/custom serializers, Json options, alternative formats, and shrinker risks. Treat source findings as candidates; inspect enclosing model/format instance before claims.

Completion: every changed encoder/decoder and model maps to one effective format instance and dependency set.

## Step 3: Configure compiler plugin and runtime

READ `references/setup-platforms.md`.

1. MATCH `org.jetbrains.kotlin.plugin.serialization` exactly to the Kotlin compiler plugin version.
2. SELECT the independently versioned runtime format artifact, normally `kotlinx-serialization-json`; keep all serialization runtime modules aligned.
3. ADD the format dependency to the narrowest owning source set; use base coordinates in common KMP source sets.
4. APPLY format-specific platform/experimental limits and Android shrinker rules.
5. VERIFY generated `.serializer()` access by compiling an annotated model and performing one encode/decode.

Completion: compiler-generated serializer and selected format work on every intended platform.

## Step 4: Model the serialized shape

READ `references/models-evolution.md`.

1. ANNOTATE only data intended for serialization; referenced custom types also need serializers.
2. RECORD each backing-field property name/type/nullability/default/required policy. Getter-only and delegated properties are not serialized by default.
3. USE stable `@SerialName` values for externally persisted fields/types and polymorphic discriminators; preserve them across source renames.
4. EXCLUDE derived/secret/transient state intentionally with `@Transient` plus a valid default where required.
5. VERIFY generic type serializers and descriptors with concrete type arguments.
6. Avoid expecting object identity/reference cycles to round-trip; kotlinx.serialization encodes plain data graphs.

Completion: descriptor and golden payload express the intended wire schema exactly.

## Step 5: Configure format behavior

For JSON, READ `references/json.md`. For CBOR, ProtoBuf, Properties, HOCON, or custom formats, READ `references/formats-security.md`.

1. CREATE one policy-specific format instance rather than scattered defaults/options.
2. DECIDE unknown-key, default, explicit-null, leniency, special-number, map-key, naming, discriminator, module, and exception-debug behavior.
3. KEEP strict parsing at untrusted boundaries unless compatibility explicitly requires relaxation.
4. BOUND input size/depth/resource use outside the serializer where the format offers no adequate limit.
5. NEVER log exception/input text containing secrets; use privacy-safe exception configuration and sanitization.

Completion: every format option has a producer/consumer/security rationale and boundary tests.

## Step 6: Implement custom or polymorphic serialization

READ `references/serializers-polymorphism.md`.

1. PREFER generated/built-in serializers.
2. USE contextual serialization for externally registered type-specific policy; use polymorphic serialization only for a declared hierarchy protocol.
3. USE sealed hierarchies for closed sets; register every open-hierarchy subtype in `SerializersModule`.
4. SERIALIZE through the intended static base type when a discriminator is required.
5. For custom `KSerializer`, keep `SerialDescriptor`, encoder calls, decoder branches, nullability, defaults, and element indexes consistent.
6. USE a unique stable descriptor serial name and test with more than one format when claiming format independence.

Completion: serializer registration, static type, discriminator, descriptor, and round-trip behavior are explicit.

## Step 7: Evolve schemas safely

1. CLASSIFY add/remove/rename/type/nullability/default/discriminator/field-number change for both old-reader/new-writer and new-reader/old-writer directions.
2. PRESERVE old serialized names with `@SerialName`; do not reuse ProtoBuf numbers or polymorphic discriminator values.
3. ADD fields with compatible defaults when old payloads must decode; test explicit `null` separately from missing.
4. KEEP unknown-key policy aligned with rolling-upgrade direction; ignoring unknown keys helps old readers but can hide misspelled/forbidden fields.
5. USE explicit migration/transforming serializers only when the compatibility matrix requires them; retain old fixtures.

Completion: old/new compatibility tests cover every supported upgrade direction and rejected payload.

## Step 8: Test observable wire behavior

READ `references/testing-troubleshooting.md`.

1. ASSERT canonical encoded bytes/text against golden fixtures; round-trip alone can hide symmetric schema drift.
2. DECODE oldest supported fixtures and payloads from other implementations.
3. TEST missing required/optional fields, explicit null, unknown/duplicate keys, defaults, malformed input, polymorphic unknown subtype, numeric boundaries, Unicode, and privacy-safe errors as applicable.
4. TEST custom serializer descriptor and encode/decode symmetry; fuzz/property-test untrusted decoders where supported.
5. For experimental binary formats, validate against an independent implementation/schema and preserve exact bytes.

Completion: tests fail on plausible wire breakage and prove supported compatibility directions.

## Step 9: Diagnose failures

1. CLASSIFY missing compiler plugin | missing serializer | module registration | static type | discriminator | field/default/null | format option | version linkage | shrinker | malformed/untrusted input.
2. REPRODUCE with the exact format instance, serializer, static type, payload, dependency version, and platform.
3. INSPECT generated serializer descriptor and registered `SerializersModule` before adding reflection/contextual fallbacks.
4. FIX schema/configuration root cause; never solve an unknown-key or subtype failure by globally weakening unrelated boundaries.
5. RE-RUN focused fixtures, round-trip, cross-version, and full module tests.

Completion: original payload succeeds or fails according to explicit schema policy with no broader relaxation.

## Step 10: Verify and report

1. COMPILE serializer generation on every intended target.
2. RUN golden encode, old-fixture decode, invalid-input rejection, polymorphic/custom serializer, and shrinker/release build where relevant.
3. INSPECT descriptor names/elements and exact encoded form.
4. COPY `assets/serialization-report.md`; fill versions, format instance/options, schema table, compatibility matrix, serializers/modules, payload fixtures, commands/results, security/privacy controls, and limitations.

## Error Handling

- `.serializer()` unresolved -> apply matching Kotlin serialization compiler plugin to the compiling module/source set and rebuild.
- `Serializer for class ... is not found` -> verify annotation/generated serializer, static type, contextual/polymorphic registration, and plugin execution.
- Unknown key -> verify payload spelling/version and boundary policy before enabling `ignoreUnknownKeys` narrowly.
- Missing field -> add/restore compatible default or migration; nullable without default is still required when absent.
- Polymorphic subtype not registered -> register it in the format's `SerializersModule` and stabilize `@SerialName`.
- Class discriminator collides with property -> rename/stabilize discriminator or property serial name; test old payloads.
- Android release fails only after shrinking -> inspect bundled rules and named companion-object keep requirements.
- Exception leaks input -> disable serialization debug input where supported and sanitize logs/errors.
