# Serialization testing and troubleshooting

## Test matrix

For each supported schema/format/platform:
1. current value -> exact canonical payload
2. canonical payload -> expected value
3. oldest supported payload -> current value
4. current payload -> old consumer, when supported
5. missing optional/required fields
6. explicit null versus absent
7. unknown/duplicate fields
8. malformed/truncated input
9. numeric/Unicode/collection boundaries
10. every polymorphic subtype plus unknown discriminator
11. custom descriptor and serializer
12. privacy-safe exception/log output

Round-trip is necessary but insufficient: encoder and decoder can share the same bug or silently change schema together.

## Common failures

- unresolved `.serializer()`: compiler plugin absent/mismatched/not applied to module
- `Serializer for class ... is not found`: referenced type lacks generated/custom/contextual/polymorphic serializer, or static type differs
- missing field: absent property has no compatible default/optional descriptor
- unknown key: payload/version mismatch or strict policy
- expected default but explicit null fails: non-null type rejects null; missing and null differ
- duplicate serial name/element: model/naming strategy collision
- polymorphic serializer not found: subtype absent from SerializersModule or wrong format instance/static base type
- discriminator collision: property serial name equals configured discriminator
- custom serializer corrupts structure: descriptor/order/index/kind differs between encoder and decoder
- works in debug, fails minified Android: named companion/serializer keep rules
- `NoSuchMethodError`/linkage: runtime modules are version-skewed or library metadata exceeds Kotlin toolchain

## Diagnosis

Capture exact payload safely, format options, serializer descriptor, static type, module registrations, versions, platform, and stack root. Minimize to one encode/decode. Fix the narrow model/format/module; do not globally enable leniency or ignore unknown keys to mask unrelated producer defects.
