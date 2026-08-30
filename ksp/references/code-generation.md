# Code generation and output ownership

Source: [KSP quickstart](https://kotlinlang.org/docs/ksp-quickstart.html) and [incremental processing](https://kotlinlang.org/docs/ksp-incremental.html).

Generate through `CodeGenerator.createNewFile(Dependencies, packageName, fileName, extensionName)` or `createNewFileByPath` where appropriate. The package/file/extension tuple is an invocation-wide identity; duplicate creation fails.

Always close streams:
```kotlin
codeGenerator.createNewFile(
    dependencies = Dependencies(aggregating = false, sourceFile),
    packageName = generatedPackage,
    fileName = generatedName,
).bufferedWriter().use { out ->
    out.append(generatedSource)
}
```

Dependency classification:
- isolating (`aggregating=false`): output changes only with declared root source(s), such as one adapter per annotated class
- aggregating (`aggregating=true`): output membership/content can change when any symbol in a wider queried set changes, such as registries/indexes/schemas

Pass every directly contributing `KSFile`. KSP traces cross-file edges created by type resolution from roots; do not add unrelated files defensively. An output with no source origin needs explicit aggregate semantics and removal tests.

Determinism: sort by stable qualified/signature key; normalize imports/member order/line endings/UTF-8; omit timestamps, machine paths, unordered set/map iteration, random values, and environment-specific comments.

Render language syntax deliberately. Escape Kotlin identifiers, avoid import collisions, preserve generic bounds/variance/nullability/suspend/receiver/visibility, and generate legal Java names/types separately. Prefer a structured writer library only when already adopted; compile generated output remains the oracle.

Generated API is product API. Test source/binary compatibility, diagnostics, and callers when names/signatures/visibility change.
