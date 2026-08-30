# API lookup examples

## Overloaded stdlib function

Question: which `map` overload applies to `Map<K,V>`?
1. Resolve `kotlin-stdlib` version and source-set platform.
2. Open `kotlin.collections.map` declaration page.
3. Select the overload whose receiver is `Map<out K,V>` and transform receives `Map.Entry<K,V>`.
4. Record `inline`, return `List<R>`, Since metadata, and source link ref.
5. Compile a typed probe if receiver inference/imports are unclear.

## Platform-specific serialization member

Question: can common code call `Json.decodeFromStream`?
1. Resolve `kotlinx-serialization-json` version.
2. Open `Json` members and find `decodeFromStream`.
3. Observe the `jvm` platform label and experimental annotation.
4. Conclude it is unavailable to `commonMain`; verify a common compile probe when material.

## Moving source link

Question: what does `CoroutineScope` guarantee in the installed coroutines version?
1. Resolve `kotlinx-coroutines-core` effective version.
2. Use the API page for contract/signature.
3. Notice whether its source link targets `master`.
4. Reopen the same source path at the dependency's release tag.
5. Use release notes and a probe for behavior changed between refs.

Examples demonstrate procedure only. Always use the current project's versions and the live official pages.
