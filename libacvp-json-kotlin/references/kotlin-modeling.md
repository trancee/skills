# Kotlin modeling with kotlinx.serialization

## Shape-first parser

Parse once to `JsonElement`, then classify:

```kotlin
val root = wireJson.parseToJsonElement(text)
val document = classifyAcvpDocument(root)
```

Use the template in `assets/AcvpEnvelope.kt`. Keep `JsonObject` at boundaries where the exact endpoint or algorithm tuple is not known. Typed decoding begins only after classification.

## Wire JSON configuration

Start strict:

```kotlin
val wireJson = Json {
    ignoreUnknownKeys = false
    isLenient = false
    explicitNulls = true
    coerceInputValues = false
    encodeDefaults = false
}
```

Configure duplicate-key rejection before this layer because kotlinx.serialization's ordinary JSON object representation cannot preserve duplicate members for later rejection. Enforce input byte/depth/count limits in the surrounding I/O layer.

## Root types

Represent heterogeneous root shapes explicitly:

```kotlin
sealed interface AcvpDocument {
    data class ProtocolEnvelope(
        val version: String,
        val payloads: List<JsonObject>,
    ) : AcvpDocument

    data class LibacvpBundle(
        val metadata: JsonObject,
        val vectorSets: List<JsonObject>,
    ) : AcvpDocument

    data class BareVectorSet(val value: JsonObject) : AcvpDocument
}
```

Do not deserialize a JWT into a data class whose generated `toString`, equality failure, debugger view, or snapshot may expose it. Retain secret-bearing metadata as opaque/redacted data or a dedicated secret type with safe rendering.

## Vector-set header

Use a shallow header to select the algorithm serializer:

```kotlin
@Serializable
data class VectorSetHeader(
    val vsId: Long,
    val algorithm: String,
    val mode: String? = null,
    val revision: String? = null,
    val testGroups: List<JsonObject>,
)
```

This is a dispatch model, not a universal vector-set model. After checking the exact tuple, decode the original object into the selected complete type.

## Parent-owned discriminators

ACVP case shapes depend on fields in ancestor objects. For example, a test case may need the vector set's `algorithm`, `mode`, and `revision` plus the group's `testType`, `direction`, or `parameterSet`.

Avoid `JsonContentPolymorphicSerializer` when the discriminator is absent from the case object. Instead:

1. Decode vector-set header.
2. Select vector-set codec by exact tuple.
3. Decode each group header.
4. Select group/case codec from the parent context.
5. Decode cases through that codec.

Represent dispatch keys with stable value types:

```kotlin
data class VectorCodecKey(
    val algorithm: String,
    val mode: String?,
    val revision: String?,
)

data class GroupCodecKey(
    val vector: VectorCodecKey,
    val testType: String,
)
```

Do not normalize case, punctuation, algorithm aliases, or missing revisions unless the selected specification defines equivalence.

## Missing, null, and defaults

ACVP schemas distinguish field absence from present values. Kotlin defaults can hide missing fields. For required wire fields, omit defaults so decoding fails. For optional fields whose presence matters, use a presence wrapper or inspect the `JsonObject` before typed decoding.

Nullable does not mean optional automatically: `value: String?` without a default remains required under generated serializers. Test missing and explicit `null` separately.

## Hex and bit strings

Keep encoded fields as strings in wire models:

```kotlin
@Serializable
data class AesCase(
    val tcId: Long,
    val key: String,
    val iv: String? = null,
    val pt: String? = null,
    val ct: String? = null,
)
```

Convert at the operation adapter after validating:

- ASCII `[0-9A-Fa-f]*` only.
- Empty allowed only by exact field schema.
- Exact declared bit length; odd hex may be valid only for a bit-oriented schema with explicit handling.
- Leading zeroes preserved.
- Decoded byte allocation bounded before conversion.

Never store wire hex as `BigInteger`: sign and leading-zero semantics change. Never use `HexFormat.parseHex` before validating the schema's bit-length rules.

## IDs and numeric ranges

Use `Long` for `vsId`, `tgId`, and `tcId`; reject negative/fractional/out-of-range values. For algorithm lengths, use `Long` when the schema does not guarantee `Int`; validate range before buffer allocation or API conversion.

For uncertain numeric contracts, inspect the raw `JsonPrimitive` first and require a canonical integer token.

## Response construction

Construct a typed response from validated request context. Keep request and response case classes distinct. This prevents accidental echo of inputs, entropy, keys, or fields prohibited in the response.

Encode to `JsonElement` for structural tests. JSON object member order is insignificant; array order and ID association are significant.
