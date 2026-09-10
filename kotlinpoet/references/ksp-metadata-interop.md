# KSP and metadata interop

## Modules and hosts

Core KotlinPoet publishes multiplatform variants currently covering JVM, JS, and WasmJS. KSP and metadata interop are JVM-specific generator-host concerns. Keep these modules in processor/tooling projects, not generated-code runtime dependencies.

Use matching versions:

```kotlin
dependencies {
    implementation("com.squareup:kotlinpoet:<version>")
    implementation("com.squareup:kotlinpoet-ksp:<version>")
}
```

Route KSP plugin/configuration, rounds, deferral, and incremental diagnostics to the `ksp` skill.

## Type parameter resolution

KSP type variables require a resolver that carries declaration scope. Create and compose resolvers from enclosing to nested declaration:

```kotlin
val classResolver = ksClass.typeParameters.toTypeParameterResolver()
val functionResolver = ksFunction.typeParameters.toTypeParameterResolver(classResolver)
val returnType = ksFunction.returnType!!.toTypeName(functionResolver)
```

Passing an empty resolver for a type that references enclosing variables can produce unresolved or incorrectly rendered types. Test class, function, nested, shadowed, bounded, and recursive type variables.

## KS conversions

Use `kotlinpoet-ksp` conversions for:

- `KSClassDeclaration.toClassName()`
- `KSType` / `KSTypeReference.toTypeName(resolver)`
- type parameters/resolvers
- annotations and modifiers where supported
- originating `KSFile` integration

Do not use `toString()`, `qualifiedName.asString()` plus manual parsing, or source display text as type syntax. KSP symbol presentation is not a stable Kotlin source renderer.

## Originating files and write path

Attach every direct contributing source:

```kotlin
val fileSpec = FileSpec.builder(packageName, fileName)
    .addOriginatingKSFile(sourceFile)
    .addType(generatedType)
    .build()

fileSpec.writeTo(
    codeGenerator = codeGenerator,
    aggregating = false,
)
```

For output derived from multiple sources, add all direct origins. KSP resolution can trace transitive symbol dependencies; do not attach every file to an isolating output for convenience.

Write through `CodeGenerator` using KotlinPoet's KSP extension. Direct `File`, `Files.write`, or arbitrary filesystem output bypasses KSP ownership, cleanup, and incrementality.

## Aggregating decision

- `aggregating = false`: output identity/content depends only on declared originating roots, commonly one annotated declaration.
- `aggregating = true`: any member of a wider set can change the output, such as a registry of all annotated declarations.

Classify from actual semantics. A single output file is not automatically aggregating; many output files are not automatically isolating.

## Rounds and deterministic order

- Process only current-round symbols.
- Return unresolved source symbols for deferral.
- Never retain KS nodes/types across rounds.
- Track already generated paths by stable semantic identity.
- Sort declarations/members before KotlinPoet construction.
- Generate each path once.

Generated-to-generated dependencies must converge. A duplicate-path guard cannot substitute for correct round logic.

## Metadata interop

KotlinPoet metadata interop produces best-effort Kotlin source stubs from metadata models. Use it for declaration/documentation/analysis workflows that tolerate approximations.

Do not use metadata stubs to:

- Reconstruct function bodies or executable implementation.
- Guarantee original formatting/comments/import aliases/type aliases.
- Reproduce source-only annotations or compiler-lowered details.
- Establish source/binary compatibility without separate ABI tools.

Pin input metadata/Kotlin versions and compile representative stubs. Record every unsupported or approximated construct in the report.
