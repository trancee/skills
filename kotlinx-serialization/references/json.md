# JSON policy

Source: [JSON overview](https://kotlinlang.org/docs/serialization-configure-json-serialization.html) and exact [Json API](https://kotlinlang.org/api/kotlinx.serialization/kotlinx-serialization-json/kotlinx.serialization.json/-json/).

Create named policy instances at system boundaries:
```kotlin
val wireJson = Json {
    ignoreUnknownKeys = true
    encodeDefaults = true
    explicitNulls = false
    classDiscriminator = "type"
    exceptionsWithDebugInfo = false
}
```

Verify option availability/stability at the selected version. In 1.11.0, structured JSON exceptions and `exceptionsWithDebugInfo` are experimental.

## Decision table

- `ignoreUnknownKeys`: rolling compatibility for additive writers; can hide misspellings/forbidden input
- `encodeDefaults`: canonical payload includes defaults versus compact omission
- `explicitNulls`: encode null fields or omit; changes distinction seen by other consumers
- `coerceInputValues`: map certain invalid/null enum values to defaults/null; can hide producer defects
- `isLenient`: accept nonstandard JSON; avoid at untrusted strict boundaries
- `allowSpecialFloatingPointValues`: permits NaN/infinities, nonstandard interoperability risk
- `allowStructuredMapKeys`: encodes nonprimitive keys as arrays, changing shape
- `prettyPrint`: presentation only but changes exact bytes/signatures
- `classDiscriminator`: public polymorphic field name; must not collide
- `namingStrategy`: bulk wire-name transformation; migration-sensitive
- `serializersModule`: contextual/polymorphic registrations
- `exceptionsWithDebugInfo`: controls inclusion of user input in exception messages

Default values are versioned behavior; configure explicitly for long-lived external protocols when stability matters.

## Boundaries

Parse untrusted input with size/depth/rate limits outside Json when needed. Avoid logging raw payload or exception debug fragments. Test duplicate keys, unknown keys, Unicode, extreme numbers, malformed nesting, and platform I/O APIs. JVM stream/kotlinx-io/Okio integrations can be experimental; check platform labels.
