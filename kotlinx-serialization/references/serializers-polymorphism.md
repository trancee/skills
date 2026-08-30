# Custom, contextual, and polymorphic serializers

Sources: [serializer guide](https://kotlinlang.org/docs/serialization-create-and-use-serializers.html) and [polymorphism](https://kotlinlang.org/docs/serialization-polymorphism.html).

## Prefer generated serializers

`Type.serializer()` returns the generated serializer. `serializer<T>()` resolves parameterized/built-in serializers; generic `Box.serializer(elementSerializer)` requires one serializer per type parameter. Collection serializers are composed from element/key/value serializers.

## Custom KSerializer

Implement only when the wire representation differs from generated structure. Keep:
- unique stable `SerialDescriptor.serialName`
- descriptor kind/elements aligned with encoder/decoder calls
- element indexes/names/optionality stable
- primitive kind matched to `encodeX`/`decodeX`
- null handling/default/unknown element behavior symmetric
- format independence unless explicitly checking format-specific encoder/decoder

Test descriptor plus golden encode/decode. Delegating to an existing serializer is safer than hand-writing composite traversal.

## Contextual

Use `@Contextual`/`@UseContextualSerialization` when serializer policy is supplied externally. Register in the exact `SerializersModule` installed on the format instance. Contextual lookup depends on static type and module registration.

## Polymorphism

Serialization is static by default: the declared/static type controls encoded properties.

- closed: `@Serializable sealed` base and serializable subclasses are known; compiler supplies hierarchy
- open: abstract/open/interface base requires explicit `polymorphic(Base::class) { subclass(...) }` registration
- encode through base type to include discriminator
- give each subtype a stable `@SerialName`; default class names change during refactors
- configure `classDiscriminator` once and prevent collision with model property serial names
- register default serializer/deserializer only with explicit unknown-subtype policy

Unregistered input subtype must fail rather than instantiate arbitrary classes. Test unknown discriminator and every registered subtype.
