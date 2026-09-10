---
name: kotlinpoet
description: "Generates, reviews, tests, and troubleshoots deterministic Kotlin source with Square KotlinPoet. Use when building FileSpec, TypeSpec, FunSpec, PropertySpec, CodeBlock, TypeName, MemberName, imports, annotations, type aliases, KSP output, metadata stubs, or compile-tested code generators. Don't use for ordinary Kotlin implementation, JavaPoet, source parsing or rewriting, compiler plugins, template engines, or KSP lifecycle work unrelated to source emission."
compatibility: "Targets KotlinPoet 2.4.0. Core supports current JVM, JS, and WasmJS artifacts; kotlinpoet-ksp and kotlinpoet-metadata remain JVM-specific. Verify the release and Kotlin/KSP compatibility before upgrades. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://square.github.io/kotlinpoet/"
  sourceVersion: "square/kotlinpoet 2.4.0@97e504bbcece8100b653c5d7d7cd1bba0a55b0b3 (2026-09-07)"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-09-10T19:10:35+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-09-10T19:10:35+02:00"
---

# KotlinPoet

## Step 1: Define the generated-source contract

1. CLASSIFY standalone generator | annotation processor | KSP processor | schema/compiler output | metadata stub | generator migration | formatting/import defect.
2. IDENTIFY input authority, output package/path, declarations, visibility, language/API targets, module/source set, public API/ABI effect, regeneration owner, incremental ownership, and consumer compilation/runtime proof.
3. READ the current [KotlinPoet documentation](https://square.github.io/kotlinpoet/), [release](https://github.com/square/kotlinpoet/releases/latest), and affected API reference before setup or migration.
4. KEEP KotlinPoet's boundary explicit: it models Kotlin files/declarations/types and renders code blocks; it does not parse or rewrite existing Kotlin expression/statement syntax.
5. ROUTE processor lifecycle, deferral, and incremental graph work to `ksp`; ordinary Kotlin behavior to `kotlin-development`; build/toolchain wiring to `kotlin-gradle`; exact symbol lookup to `kotlin-api-reference`.

Completion: input-to-output mapping, owning module/processor, generated API, deterministic order, incremental dependency class, and compilation targets are explicit.

## Step 2: Inspect the generator project

RUN from the target repository root:
```bash
python3 scripts/inspect-project.py --root . --json
```

1. CONFIRM KotlinPoet artifacts/versions, builders/specs, format placeholders, raw code/string interpolation, type/name/import handling, KSP/metadata interop, originating files, aggregating mode, output path, ordering, timestamps/absolute paths, and compile tests.
2. TREAT findings as review leads; inspect each complete builder/write path before concluding a defect.
3. READ `references/spec-model.md` before changing declaration structure. READ `references/code-blocks-imports.md` before changing bodies, format strings, names, or imports.

Completion: every generated path and public declaration traces to structured input, one builder, one writer, and one behavioral test surface.

## Step 3: Configure the narrowest artifact

1. USE `com.squareup:kotlinpoet:<version>` in Gradle/KMP so variant resolution selects the platform artifact. Use `com.squareup:kotlinpoet-jvm:<version>` for Maven or direct JVM resolution where Gradle metadata is unavailable.
2. ADD `com.squareup:kotlinpoet-ksp:<version>` only to JVM-hosted KSP processor code that converts KS symbols or writes through `CodeGenerator`.
3. ADD metadata interop only for its specific best-effort stub use case; keep it JVM-hosted and out of consumers/runtime artifacts.
4. ALIGN all KotlinPoet modules to one pinned version through the repository's version catalog/dependency management.
5. KEEP KotlinPoet in generator/processor/build tooling scopes; generated-code consumers should depend only on APIs referenced by emitted source.

Completion: one pinned KotlinPoet version and only required modules appear on generator host classpaths.

## Step 4: Build the declaration model

READ `references/spec-model.md`.

1. CONSTRUCT `FileSpec`, `TypeSpec`, `FunSpec`, `PropertySpec`, `ParameterSpec`, `AnnotationSpec`, and `TypeAliasSpec` from semantic inputs rather than concatenated source.
2. REPRESENT types with `ClassName`, `TypeName`, `ParameterizedTypeName`, `TypeVariableName`, wildcard/lambda types, and nullability; preserve annotations and modifiers intentionally.
3. REPRESENT referenced top-level members with `MemberName`; pass declarations/specs to `%N` instead of duplicating emitted names.
4. SET package, file name, visibility, modifiers, receivers, context parameters, type variables, bounds, constructors, supertypes, and KDoc from the actual API contract.
5. USE explicit visibility emitted by KotlinPoet for explicit-API portability; never strip it only to match abbreviated documentation examples.
6. KEEP one deterministic owner for each output path; reject duplicate `FileSpec` names before writing.

Completion: every emitted declaration and type is structurally represented and compiles without raw declaration text.

## Step 5: Compose safe code blocks and imports

READ `references/code-blocks-imports.md`.

1. USE `%S` for quoted/escaped string constants, `%P` only when preserving Kotlin `$` templates is intentional, `%T` for types/imports, `%M` for members/imports, `%N` for names, and `%L` only for trusted prebuilt literals/specs/code.
2. NEVER place untrusted or arbitrary strings into format strings or `%L`; pass values as arguments with the correct placeholder.
3. USE one placeholder addressing style per formatting operation: relative, positional, or named. Keep argument counts/types exact.
4. USE `CodeBlock.Builder` control-flow and indentation APIs for statements/branches/loops; do not hand-assemble braces or indentation.
5. USE `NameAllocator` and structured names for collisions/keywords. Add explicit aliased imports only when the API contract requires stable aliases.
6. FOR KotlinPoet 2.x wrapping, use `♢` where a legal wrap opportunity is intended; ordinary spaces no longer create wrapping points. Apply project formatting after generation only when byte-stable and configured.

Completion: emitted code contains correctly escaped literals/templates, resolvable imports, collision-safe names, and deterministic layout.

## Step 6: Integrate KSP or metadata only when required

READ `references/ksp-metadata-interop.md`.

1. FOR KSP, compose enclosing/child `TypeParameterResolver` instances and convert KS declarations/types/annotations with `kotlinpoet-ksp` rather than copying display strings.
2. ADD every contributing `KSFile` as an originating file and call `FileSpec.writeTo(CodeGenerator, aggregating = ...)`; never write processor output directly to arbitrary filesystem paths.
3. SET `aggregating` from the true input dependency set: per-symbol output is usually isolating; global registries depend on all contributing inputs.
4. SORT symbols and members before emission; do not cache KSP nodes/types across rounds.
5. FOR metadata interop, generate only documented best-effort Kotlin stubs and test known losses/approximations. Never claim reconstruction of executable implementation.

Completion: KSP outputs have correct origins/aggregation and metadata-derived output stays within documented stub fidelity.

## Step 7: Make output deterministic and maintainable

1. SORT maps, sets, symbols, annotations, members, and files by stable semantic keys before building specs.
2. EXCLUDE timestamps, random IDs, machine paths, nondeterministic hashes, environment-dependent headers, and unordered iteration from output bytes.
3. DERIVE package/file/declaration names through one collision-aware policy and validate identifiers before construction.
4. MAKE regeneration cleanly replace owned outputs and remove stale files after input deletion/rename; generated sources are never manually edited.
5. KEEP generator comments/KDoc limited to stable provenance and user-facing contract; do not embed build paths, secrets, or volatile tool output.
6. RUN the repository formatter only if its version/configuration is pinned and repeated generation plus formatting is byte-identical.

Completion: identical semantic inputs produce identical path sets and bytes across clean, incremental, machine, and input-order variations.

## Step 8: Compile and behavior-test generated code

READ `references/testing-determinism.md`.

1. ASSERT exact golden source for deliberate generated API/wire contracts, including imports, visibility, names, annotations, and signatures.
2. COMPILE generated source with the consumer's Kotlin language/API/JVM/target settings; a text snapshot alone is insufficient.
3. EXECUTE generated behavior or compile a consumer callsite that proves the emitted API where runtime execution applies.
4. TEST keywords, collisions, aliased imports, nested/generic/nullable/lambda types, type aliases, annotations/KDoc escaping, string templates, empty/maximal declarations, and unsupported inputs.
5. FOR KSP, compare clean versus incremental add/change/remove/rename output paths and bytes, then compile every consuming target/variant.
6. REGENERATE twice with permuted input order and compare output manifests/digests.
7. COPY `assets/kotlinpoet-report.md`; record versions, inputs, outputs, spec model, placeholders, KSP origins/aggregation, deterministic matrix, compile/runtime commands, and limitations.

Completion: golden, compile, consumer/runtime, and determinism checks cover every changed generator branch and target.

## Error Handling

- Unresolved import or ambiguous symbol -> replace text with `ClassName`/`TypeName`/`MemberName`, inspect collisions, and add a deliberate alias only if required.
- Generated string/template is invalid -> choose `%S` for a literal or `%P` for intentional template preservation; never patch escaping after rendering.
- Placeholder count/type error -> use one addressing style and align every argument with `%L/%N/%S/%P/%T/%M` contract.
- Line no longer wraps after KotlinPoet 2.x upgrade -> add `♢` at legal wrap sites or run a pinned formatter; ordinary spaces do not wrap.
- KSP output is stale or over-invalidated -> fix originating `KSFile` set and `aggregating` value, then compare clean and incremental removal/rename cases.
- Duplicate generated path -> establish one stable owner and deduplicate semantic inputs before `writeTo`.
- Golden passes but consumer fails -> fix the structured type/member/API model and compile generated source in the real consumer configuration.
- Metadata stub loses implementation detail -> accept/document the best-effort stub boundary or use a source/bytecode tool designed for the required fidelity.

## Official references

- Documentation: https://square.github.io/kotlinpoet/
- Repository: https://github.com/square/kotlinpoet
- API reference: https://square.github.io/kotlinpoet/2.x/kotlinpoet/
