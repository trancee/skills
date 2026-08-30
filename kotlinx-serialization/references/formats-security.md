# Alternative formats and security

Source: [alternative/custom formats](https://github.com/Kotlin/kotlinx.serialization/blob/master/docs/formats.md).

JSON is stable. CBOR, ProtoBuf, Properties, HOCON, and custom format APIs are experimental in current docs.

## CBOR

Decide definite/indefinite lengths, ByteArray major type (`@ByteString`), tags/labels, class-as-array encoding, unknown keys, and COSE requirements. These options alter bytes. Verify against RFC 8949 and an independent decoder. Preserve byte fixtures.

## ProtoBuf

kotlinx.serialization uses proto2-like required/optional semantics. Stabilize `@ProtoNumber`; choose integer type; default empty collections for absent repeated fields; avoid relying on unsupported protobuf types/features. Generate/compare schema when interoperating with other languages.

## HOCON and Properties

HOCON is JVM-only. Properties flatten structure and can lose distinctions unsupported by its representation. Test nested, nullable, collection, and key escaping behavior.

## Custom formats

Custom Encoder/Decoder work at primitive/structure protocol level and are experimental. Implement descriptor-driven behavior, collection sizes, sequential/indexed decoding, null markers, unknown indexes, and nested structures. A decoder must reject malformed/truncated inputs without unbounded allocation/recursion.

## Security/privacy

- cap payload bytes, nesting, collection/string lengths, and processing time externally where needed
- validate semantic ranges after decoding; type correctness is not business validation
- keep polymorphic subtype allowlists explicit
- avoid arbitrary class loading/reflection from discriminator text
- do not log raw untrusted payloads or debug-rich exceptions
- fuzz custom/binary decoders and exercise truncation, duplicate/conflicting fields, integer boundaries, invalid UTF, tag/field abuse
- verify Android shrinker output because missing serializers can be release-only
