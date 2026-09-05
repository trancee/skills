# Algorithm dispatch and handler reading

## Source triangulation

For each supported tuple:

1. READ the current algorithm specification linked by the [NIST supported index](https://pages.nist.gov/ACVP/#supported).
2. PIN the exact libacvp source revision.
3. FIND the `alg_tbl` entry in `src/acvp.c` for algorithm name, mode, default revision, and handler.
4. READ the matching `src/acvp_<algorithm>.c` handler for required/optional fields, type checks, response construction, and test-type branches.
5. READ matching `test/json/<algorithm>/*.json` only alongside its unit test expectation.
6. RECORD differences between normative current schema and the pinned libacvp implementation; choose one explicit producer contract per parser.

libacvp uses Parson calls such as `json_object_get_*`, `acvp_tc_json_get_*`, and response `json_object_set_*`. A field read in a handler reveals what that code path expects; it does not prove every algorithm revision uses the same field.

## Dispatch table

Use a closed registry rather than reflection or permissive polymorphism:

```kotlin
interface VectorSetCodec {
    fun decodeRequest(value: JsonObject): TypedVectorSet
    fun encodeResponse(value: TypedResponse): JsonObject
}

val codecs: Map<VectorCodecKey, VectorSetCodec> = mapOf(
    VectorCodecKey("ACVP-AES-CBC", null, "1.0") to AesCbc10Codec,
    VectorCodecKey("ML-DSA", "sigGen", "FIPS204") to MlDsaSigGenCodec,
)
```

Use exact strings from the selected specification/source. If a revision is optional in an artifact, resolve it only through a documented producer rule; otherwise reject it.

## AES family example

A symmetric vector set commonly owns `algorithm`, `revision`, and `testGroups`. A group can own:

- `tgId`
- `testType`
- `direction`
- `keyLen`
- algorithm/mode-specific IV, tag, payload, tweak, or Monte Carlo properties

A case can own:

- `tcId`
- `key`
- `iv`
- `pt` or `ct`
- algorithm-specific AAD/tag/tweak fields

The response differs by direction and test type. Authenticated decryption can emit `testPassed` instead of plaintext on failure. Model that result as an explicit sealed outcome, not nullable output ambiguity.

## Hash/XOF example

Hash handlers branch by test type and revision. Fields can include:

- Group: `tgId`, `testType`, `mctVersion`, `minOutLen`, `maxOutLen`
- Case: `tcId`, `msg`, `len`, `outLen`, or nested `largeMsg`
- Response: digest/output field, and for MCT a nested `resultsArray`

AFT, MCT, VOT, and LDT are different operation models. Do not merge them into a class with many nullable fields. LDT can describe data generation rather than embedding an ordinary message string; preserve the nested structure and validate large lengths before allocation.

## ML-DSA example

The inspected libacvp ML-DSA handler dispatches from vector `mode` and group fields including:

- `testType`
- `parameterSet`
- `signatureInterface`
- `preHash` or `externalMu`
- `deterministic`

Case fields vary by mode and can include:

- `seed`
- `message` or `mu`
- `hashAlg`
- `context`
- `pk`, `sk`
- `rnd`
- `signature`

Responses differ among `keyGen`, `sigGen`, and `sigVer`. Keep mode-specific case/response types. Treat seed, private key, randomizer, and intermediate message representative as sensitive according to workflow.

## Registration domains

Registration capability models frequently include value domains represented as:

```json
[128, 192, 256]
```

or:

```json
[{ "min": 8, "max": 65536, "increment": 8 }]
```

Model this as a sealed domain type selected at the registration field, not as `List<JsonElement>` propagated into application logic. Validate min/max/increment consistency and current algorithm constraints.

## Unknown fields and evolution

Strict decoding exposes schema drift. Handle deliberate forward compatibility at a named boundary:

1. Parse to `JsonObject`.
2. Validate dispatch tuple.
3. Compare observed keys with the exact codec's allowed/required sets.
4. Reject unknown security-relevant fields.
5. If policy allows benign extension fields, preserve them separately and never let them influence cryptographic execution silently.

Never enable global `ignoreUnknownKeys` merely to parse a newer server revision.
