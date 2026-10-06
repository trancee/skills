# Processor and symbol API

Sources: [overview](https://kotlinlang.org/docs/ksp-overview.html) and [symbol model](https://kotlinlang.org/docs/ksp-additional-details.html).

Entry points:
- `SymbolProcessorProvider.create(environment)` -> one processor instance
- `SymbolProcessor.process(resolver)` -> deferred `List<KSAnnotated>`
- `finish()` -> successful finalization
- `onError()` -> cleanup after reported/thrown error

Environment provides options, Kotlin version, code generator, logger, and platform info. Resolver exposes source/generated symbols and declarations.

Prefer narrow roots:
- `getSymbolsWithAnnotation(fqName)` for annotations
- `getClassDeclarationByName()` for one known type
- `getDeclarationsFromPackage()` for a defined package contract
- `getAllFiles()` only for genuinely global processing
- `getNewFiles()` for files generated in the prior round

KSP models declarations/types, not expressions/statements. It reads Java and Kotlin through one model, but language differences remain.

Resolution is explicit and expensive: inspect `KSTypeReference.element`/referenced names before `resolve()`. After resolution handle `KSType.isError`, declaration/type parameters, arguments/variance/star projections, nullability, aliases, flexible/platform types, expect/actual, visibility, local/anonymous declarations, and missing `qualifiedName`/`containingFile`.

Use `validate()` only as broad convenience. Define the exact required properties; defer only source symbols that can become valid from later generated files. Classpath/library error types cannot be fixed by another source-generation round.

Diagnostics use `KSPLogger.error/warn/info` and attach the closest offending `KSNode`. Avoid dumping symbol/source content that may contain secrets.

## Backing fields (KSP 2.3.12+)

KSP 2.3.12 explicitly models Kotlin/Java backing fields for properties ([#2873](https://github.com/google/ksp/issues/2873)). New behavior is opt-in so existing processors are not broken.

After opt-in, observe:
- `Resolver.getSymbolsWithAnnotation` returns a `KSBackingField` when the annotation targets a field (previously a `KSProperty`).
- `Resolver.effectiveJavaModifiers` returns fewer modifiers for a `KSPropertyDeclaration` that has a backing field, since JVM-specific annotations attach to the backing field; call it on the property's `KSBackingField` for JVM modifiers.
- Java fields are modeled as properties with backing fields; some modifiers move to the backing field.
- `KSBackingField.property` identifies the owning property; don't substitute the field declaration's name/identity for that property's declaration.

Opt in with both steps simultaneously (neither alone is supported):
1. Create the `SymbolProcessor`, call `environment.registerProcessorForNewFeatures(processor)` exactly once, then return that same instance from the provider. The registration takes the processor, not a no-argument opt-in.
2. move `KSVisitor` implementations to `KSVisitorNext`; if extending a KSP-provided visitor, extend `KSTopDownVisitor(enableNewFeatures = true)` and override `visitBackingField`.

Sources: [KSP 2.3.12 release](https://github.com/google/ksp/releases/tag/2.3.12), [registration API](https://github.com/google/ksp/blob/a3c38590913b863cc6b73b41d54ff8afa625f642/api/src/main/kotlin/com/google/devtools/ksp/processing/SymbolProcessorEnvironment.kt), [visitor contract](https://github.com/google/ksp/blob/a3c38590913b863cc6b73b41d54ff8afa625f642/api/src/main/kotlin/com/google/devtools/ksp/visitor/KSTopDownVisitor.kt).
