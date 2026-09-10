# Code blocks, placeholders, names, imports, and layout

## Placeholder contract

| Placeholder | Use | Security/correctness rule |
| --- | --- | --- |
| `%S` | Kotlin string literal | Quotes/escapes content, including `$`; default for data strings |
| `%P` | String template content | Preserves `$` references intentionally; use only for trusted template design |
| `%T` | `TypeName`/class/type | Enables import and collision handling |
| `%M` | `MemberName` | Enables top-level member import and collision handling |
| `%N` | name or named spec | Escapes identifiers and keeps declaration references synchronized |
| `%L` | literal/spec/code block | Inserts trusted code-like content without string escaping |
| `%%` | percent sign | Consumes no argument |

`%L` is not a general string placeholder. An arbitrary string passed to `%L` can create invalid code or source injection. Prefer `%S`, `%N`, `%T`, or a validated prebuilt `CodeBlock`.

## Addressing styles

Use exactly one style per formatting call:

```kotlin
// Relative.
addStatement("return %T(%S)", Widget::class, value)

// Positional.
add("return %1T(%2S)", Widget::class, value)

// Named.
addNamed("return %widget:T(%value:S)", mapOf("widget" to widget, "value" to value))
```

Do not mix relative, positional, and named placeholders in one operation. Named arguments use lowercase-leading names and explicit placeholder suffixes.

## Strings versus templates

```kotlin
addStatement("println(%S)", externalText)       // literal text
addStatement("println(%P)", "Hello, \$name") // intentional Kotlin template
```

Choose `%P` only when emitted code should evaluate template expressions at runtime and the template is generator-owned. External/user/schema prose normally uses `%S`.

## Control flow

Use structured builder methods:

```kotlin
val code = CodeBlock.builder()
    .beginControlFlow("if (%N == null)", valueParameter)
    .addStatement("return %S", "missing")
    .nextControlFlow("else")
    .addStatement("return %N.toString()", valueParameter)
    .endControlFlow()
    .build()
```

Use statements for complete logical statements and explicit `CodeBlock` composition for expressions. Avoid concatenating indentation/braces/newlines around fragments.

## Imports and collisions

- Pass `TypeName` through `%T` and top-level `MemberName` through `%M`.
- Let `FileSpec` resolve normal imports.
- Use `addAliasedImport` when two symbols collide or a stable alias is a deliberate source contract.
- Use `NameAllocator` when external names can collide with keywords, locals, generated members, or each other.
- Keep the allocator's tags tied to semantic identity, not input position.
- Test nested class/simple-name collisions and a member whose name matches an imported type/member.

Do not pre-render imports or shorten qualified names manually. KotlinPoet needs structured symbols to choose correct imports.

## Keywords and identifiers

Validate source-language naming policy before allocation. `%N` and structured spec names handle escaping, but accepting every external string as a public Kotlin identifier often produces unstable APIs. Define normalization, collisions, case, reserved words, Unicode policy, and backwards compatibility in the generator contract.

## Layout and wrapping

KotlinPoet 2.x no longer treats ordinary spaces as wrap opportunities. Insert the space-like `♢` marker in format strings where KotlinPoet may legally wrap. Keep explicit newlines for required breaks and builder indentation for nesting.

If the project formats generated code afterward:

1. Pin formatter/version/configuration.
2. Run it through the generator task, not manually.
3. Include formatter inputs/outputs in incremental/cache ownership.
4. Prove generate-format-generate-format produces identical bytes.

Correct compilation and semantics outrank cosmetic wrapping.

## Safe composition

Prefer reusable typed fragments:

```kotlin
fun callMember(receiver: CodeBlock, member: MemberName): CodeBlock =
    CodeBlock.of("%L.%M()", receiver, member)
```

Here `%L` is safe because the argument is already a trusted `CodeBlock`, not raw external text. Make APIs accept `CodeBlock`, `TypeName`, `MemberName`, or named specs rather than strings when callers supply source concepts.
