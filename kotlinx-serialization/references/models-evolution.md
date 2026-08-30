# Models and schema evolution

## Generated shape

`@Serializable` generates a serializer. Properties with backing fields participate by default; getter-only and delegated properties do not. Referenced custom classes require serializers. Generic serializers require a serializer for every type argument.

Defaults make a missing field optional during decoding. Nullable without a default is still required when absent. Explicit `null` for a non-null property fails even when it has a default unless an explicit coercion policy applies.

`@Transient` removes a property and generally requires a default. `@SerialName` changes/stabilizes the external name. `@EncodeDefault` and format `encodeDefaults` control whether default-valued fields are emitted.

Serialization preserves values, not arbitrary object identity: repeated references encode independently and cycles are not reconstructed automatically.

## Compatibility matrix

For every change test:
- old reader <- new writer
- new reader <- old writer

Typical effects:
- add field with default: old payload can feed new reader; old reader needs unknown-key tolerance for new writer
- add required field/no default: old payload fails new reader
- rename source property with same `@SerialName`: wire-compatible
- rename/remove serial name: wire-breaking without migration
- non-null -> nullable: often reader-relaxing, but emitted null can break old readers
- nullable -> non-null: breaks payloads containing null/missing without compatible default/coercion
- type/representation change: requires migration/dual decoder unless formats are wire-compatible
- change polymorphic type name/discriminator: breaks stored subtype payloads
- reorder JSON properties: semantic JSON usually survives, but golden/text consumers may not

Keep golden fixtures from every supported schema version. Round-trip with one current serializer does not test evolution.

## ProtoBuf

Assign stable `@ProtoNumber` values; never renumber/reuse removed numbers. Select integer encoding intentionally. Empty repeated/map fields are indistinguishable from missing, so Kotlin collections need compatible defaults such as `emptyList()` when absence is valid. Validate generated/manual schema against non-Kotlin consumers.
