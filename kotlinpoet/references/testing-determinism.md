# Testing and deterministic generation

## Proof layers

| Claim | Evidence |
| --- | --- |
| Intended source contract | Reviewed exact golden `.kt` output |
| Kotlin syntax/type correctness | Compile generated source with consumer settings |
| Generated API usability | Compile real consumer callsite |
| Runtime behavior | Execute generated code against representative inputs |
| Deterministic generator | Equal path manifest and bytes under repeat/permuted runs |
| Incremental correctness | Clean equals add/change/remove/rename outputs |
| KSP ownership | Correct originating files, aggregation, and stale-file removal |

No single layer replaces the others. Snapshot-only tests can preserve invalid code; compile-only tests can miss wrong names/imports/visibility/API shape.

## Golden source

Keep exact expected source when formatting and declaration shape are part of the generator contract. Assert:

- Package and file annotations.
- Imports and aliases.
- Explicit visibility/modifiers.
- Type/function/property signatures.
- Annotations and KDoc.
- Bodies, literals, string templates, and control flow.
- Line endings and terminal newline.

Update goldens only after reviewing the semantic API diff. Avoid assertions that merely check substrings or nonempty output.

## Compile and consumer tests

Compile with the same:

- Kotlin language/API version.
- JVM toolchain/target or JS/Wasm target.
- Explicit API mode.
- Opt-ins/compiler flags.
- Dependencies and source-set visibility.

Compile a consumer callsite for public generated APIs. Execute behavior where the generator emits nontrivial runtime logic. Test diagnostics for rejected generator inputs separately.

## Edge-case matrix

Exercise branches for:

- Kotlin keywords and invalid external identifiers.
- Duplicate/simple-name/member/import collisions.
- Nested classes and aliases.
- Nullable, generic, bounded, projected, recursive, and lambda types.
- Receivers/context parameters/suspend functions where supported.
- Annotation use-site targets and arguments.
- KDoc containing `$`, `*/`, links, brackets, Unicode, and newlines.
- `%S` strings with quotes, slash, control characters, dollar signs, and multiline text.
- `%P` intentional templates.
- Empty input and maximal supported member counts/depths.
- Unsupported/lossy KSP or metadata types.

## Determinism matrix

For one fixed semantic input:

1. Generate in a clean directory; record sorted relative paths and SHA-256.
2. Generate again without changes; require the same manifest and bytes.
3. Permute input discovery order; require the same output.
4. Run on another working directory/machine when available; reject leaked absolute paths.
5. Change one input; require only semantically owned output changes.
6. Remove/rename an input; require stale outputs disappear.
7. Restore input; require original bytes.

Never embed wall-clock time, random UUIDs, object identity/hash iteration, temporary paths, hostname, locale-sensitive ordering, or platform line endings.

## KSP incremental matrix

Test clean and incremental:

- Add one originating symbol.
- Change its name/type/annotation.
- Remove it.
- Rename/move its source file.
- Change an unrelated symbol.
- Change one member of an aggregate registry.
- Generate a symbol consumed in a later round.

Compare final generated trees to clean builds after each mutation. Inspect KSP logs/graphs if invalidation differs; fix origin/aggregation rather than deleting build caches as a solution.

## Formatting

KotlinPoet output need only be valid and stable; cosmetic formatting is not proof. If a formatter is required, include it in the deterministic matrix. Test KotlinPoet 2.x `♢` wrap points and widths relevant to the contract.

## Report

Copy `assets/kotlinpoet-report.md` and capture exact generator/library/Kotlin/KSP versions, input/output manifests, goldens, compile/runtime tasks, incremental changes, target matrix, and limitations.
