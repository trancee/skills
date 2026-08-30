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
