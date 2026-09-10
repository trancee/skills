# KotlinPoet declaration and type model

## Spec hierarchy

Use one structured spec for each Kotlin construct:

| Kotlin source construct | KotlinPoet model |
| --- | --- |
| `.kt` file, package, imports, file annotations | `FileSpec` |
| class, interface, object, enum, annotation class, anonymous type | `TypeSpec` |
| function, constructor, getter/setter | `FunSpec` |
| property | `PropertySpec` |
| function/constructor parameter | `ParameterSpec` |
| annotation use | `AnnotationSpec` |
| type alias | `TypeAliasSpec` |
| body/expression/initializer/KDoc fragment | `CodeBlock` |

Create declarations from semantic data. Raw code belongs only inside a narrowly scoped trusted `CodeBlock`, not around entire declarations.

## Names and types

Prefer:

- `ClassName(packageName, simpleNames...)` for declared/importable classes and nested classes.
- `TypeName` variants for nullable/annotated types.
- `ParameterizedTypeName` for generic instantiations.
- `TypeVariableName` for declared type parameters and bounds.
- `WildcardTypeName` for projections.
- `LambdaTypeName` for function/suspend/receiver types.
- `MemberName` for top-level functions/properties/operators referenced from code.
- `NameAllocator` for generated local/member names derived from external inputs.

Do not use `ClassName.bestGuess()` when the producer already knows package/nesting. It parses a textual convention and can guess the wrong boundary. Carry symbol identity as structured data.

## File construction

```kotlin
val widget = ClassName("com.example.api", "Widget")

val file = FileSpec.builder("com.example.generated", "WidgetFactory")
    .addFunction(
        FunSpec.builder("newWidget")
            .addModifiers(KModifier.PUBLIC)
            .returns(widget)
            .addStatement("return %T()", widget)
            .build(),
    )
    .build()
```

Let KotlinPoet collect imports through `%T`/`%M` and spec types. Avoid manual fully qualified names in `CodeBlock` unless the emitted source contract deliberately requires them.

## Functions and constructors

Model:

- Name and visibility.
- Type variables and bounds.
- Receiver/context parameters where supported by the selected release.
- Parameters, defaults, `vararg`, annotations, modifiers.
- Return type.
- Exceptions/platform annotations only when part of the contract.
- Body and KDoc.

Use `FunSpec.constructorBuilder()` for constructors, then attach to `TypeSpec`. For a primary-constructor property, create both the constructor `ParameterSpec` and matching `PropertySpec` deliberately; KotlinPoet does not infer semantic linkage from equal strings.

## Properties

Set type, mutability, visibility, modifiers, receiver, initializer/delegate, accessors, annotations, and KDoc explicitly. Use `%N` to refer to the constructor parameter or another spec:

```kotlin
val nameParameter = ParameterSpec.builder("name", STRING).build()
val nameProperty = PropertySpec.builder("name", STRING)
    .initializer("%N", nameParameter)
    .build()
```

## Type declarations

Choose the exact `TypeSpec` builder. Preserve:

- Primary/secondary constructors.
- Superclass and constructor arguments.
- Superinterfaces/delegation.
- Type variables.
- Enum constants and anonymous bodies.
- Nested types/members/initializer blocks.
- Data/value/sealed/inner/fun-interface/expect/actual modifiers supported by the target language/API.

Reject structurally invalid combinations in the generator input model before calling builders. Do not depend on the Kotlin compiler as the first validation layer for known domain invariants.

## Annotations and KDoc

Build annotations with `AnnotationSpec`; pass class references with `%T` and member values with typed placeholders. Track use-site target separately where required.

KDoc is code-like formatted content. Escape external prose through `%L` only after treating it as trusted text content appropriate for KDoc, and test closing comment sequences, brackets, links, dollar signs, and newlines. Never allow arbitrary input to terminate KDoc and inject source.

## Type reflection conversions

Use `KClass.asClassName()`, Java/Kotlin reflection `asTypeName()`, or platform conversion APIs only when the generator truly receives reflection types. Reflection models can lose source-level aliasing or annotations. For KSP, use `kotlinpoet-ksp` conversions and a `TypeParameterResolver` instead.

## Output ownership

One generator invocation may emit many files, but each `(packageName, fileName)` must have exactly one owner. Establish this before building:

1. Normalize semantic identity.
2. Allocate collision-safe Kotlin names.
3. Sort declarations.
4. Detect duplicate output paths.
5. Build and write once.
