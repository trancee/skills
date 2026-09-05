package example.acvp

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.longOrNull

val AcvpWireJson = Json {
    ignoreUnknownKeys = false
    isLenient = false
    explicitNulls = true
    coerceInputValues = false
    encodeDefaults = false
}

sealed interface AcvpDocument {
    data class ProtocolEnvelope(
        val version: String,
        val payloads: List<JsonObject>,
    ) : AcvpDocument

    data class LibacvpBundle(
        val metadata: SensitiveJsonObject,
        val vectorSets: List<JsonObject>,
    ) : AcvpDocument

    data class BareVectorSet(val value: JsonObject) : AcvpDocument
}

class SensitiveJsonObject private constructor(private val value: JsonObject) {
    fun <T> use(block: (JsonObject) -> T): T = block(value)

    override fun toString(): String = "SensitiveJsonObject(<redacted>)"

    companion object {
        fun wrap(value: JsonObject): SensitiveJsonObject = SensitiveJsonObject(value)
    }
}

@Serializable
data class VectorSetHeader(
    val vsId: Long,
    val algorithm: String,
    val mode: String? = null,
    val revision: String? = null,
    val testGroups: List<JsonObject>,
)

data class VectorCodecKey(
    val algorithm: String,
    val mode: String?,
    val revision: String?,
)

fun parseAcvpDocument(text: String): AcvpDocument =
    classifyAcvpDocument(AcvpWireJson.parseToJsonElement(text))

fun classifyAcvpDocument(root: JsonElement): AcvpDocument = when (root) {
    is JsonObject -> {
        requireVectorSetShape(root, "$")
        AcvpDocument.BareVectorSet(root)
    }

    is JsonArray -> classifyArray(root)
    else -> error("ACVP root must be an object or array")
}

private fun classifyArray(root: JsonArray): AcvpDocument {
    require(root.isNotEmpty()) { "ACVP array root must not be empty" }
    val objects = root.mapIndexed { index, value ->
        value as? JsonObject ?: error("ACVP root[$index] must be an object")
    }
    val first = objects.first()
    val version = first.stringOrNull("acvVersion")
    if (version != null) {
        require(first.keys == setOf("acvVersion")) {
            "Protocol header must contain only acvVersion"
        }
        return AcvpDocument.ProtocolEnvelope(version, objects.drop(1))
    }

    if (first.isLibacvpMetadata()) {
        val vectors = objects.drop(1)
        vectors.forEachIndexed { index, value ->
            requireVectorSetShape(value, "$[${index + 1}]")
        }
        return AcvpDocument.LibacvpBundle(SensitiveJsonObject.wrap(first), vectors)
    }

    error("Unsupported ACVP array: missing protocol header or libacvp metadata")
}

fun decodeVectorSetHeader(value: JsonObject): VectorSetHeader {
    requireVectorSetShape(value, "vectorSet")
    return AcvpWireJson.decodeFromJsonElement(VectorSetHeader.serializer(), value)
}

fun codecKey(header: VectorSetHeader): VectorCodecKey =
    VectorCodecKey(header.algorithm, header.mode, header.revision)

fun requireHex(value: String, bitLength: Long, allowEmpty: Boolean = false): String {
    require(bitLength >= 0) { "bit length must be nonnegative" }
    require(value.isNotEmpty() || allowEmpty) { "hex value must not be empty" }
    require(value.all { it in '0'..'9' || it in 'a'..'f' || it in 'A'..'F' }) {
        "hex value contains non-ASCII-hex characters"
    }
    require(bitLength <= Int.MAX_VALUE.toLong() * 4L) { "hex value exceeds local size limit" }
    require(value.length.toLong() * 4L == bitLength) {
        "hex length does not match declared bit length"
    }
    return value
}

private fun requireVectorSetShape(value: JsonObject, path: String) {
    requireInteger(value["vsId"], "$path.vsId")
    require(!value.stringOrNull("algorithm").isNullOrEmpty()) {
        "$path.algorithm must be a nonempty string"
    }
    require(value["testGroups"] is JsonArray) { "$path.testGroups must be an array" }
}

private fun requireInteger(value: JsonElement?, path: String): Long {
    val primitive = value as? JsonPrimitive ?: error("$path must be an integer")
    require(!primitive.isString) { "$path must be an integer, not a string" }
    return primitive.longOrNull?.also { require(it >= 0) { "$path must be nonnegative" } }
        ?: error("$path must fit in Long")
}

private fun JsonObject.stringOrNull(name: String): String? {
    val value = this[name] as? JsonPrimitive ?: return null
    return if (value.isString) value.content else null
}

private fun JsonObject.isLibacvpMetadata(): Boolean =
    "url" in this || "jwt" in this || "vectorSetUrls" in this ||
        (this["isSample"] as? JsonPrimitive)?.booleanOrNull != null
