# Library and runtime integration

Sources: Kotlin 2.4.10 [`PowerAssert`](https://github.com/JetBrains/kotlin/blob/v2.4.10/plugins/power-assert/power-assert-runtime/src/commonMain/kotlin/kotlin/powerassert/PowerAssert.kt) and [`CallExplanation`](https://github.com/JetBrains/kotlin/blob/v2.4.10/plugins/power-assert/power-assert-runtime/src/commonMain/kotlin/kotlin/powerassert/CallExplanation.kt).

`@PowerAssert` has BINARY retention and marks a function whose enabled consumer calls can be transformed. The library module must compile its intrinsic-aware body with the plugin/runtime; the consumer module must apply the compiler plugin at the call site.

`PowerAssert.explanation: CallExplanation?` is valid only inside an annotated function. Its runtime getter throws `NotImplementedError` when the required compiler transformation is absent.

Preserve the assertion API's contract and failure behavior:

```kotlin
@OptIn(ExperimentalPowerAssert::class)
@PowerAssert
fun verify(
    condition: Boolean,
    @PowerAssert.Ignore message: String? = null,
) {
    if (!condition) {
        val explanation = PowerAssert.explanation
        val rendered = explanation?.toDefaultMessage() ?: message ?: "Verification failed"
        throw AssertionError(rendered)
    }
}
```

Apply `@PowerAssert.Ignore` to a value parameter or a parameter type whose values should not enter the explanation. Use it for message lambdas, DSL builders, secrets, or noisy receiver types only when omission is intentional.

`CallExplanation` contains full call source, base offset, and arguments in parameter order. Each argument may be null for implicit/default/ignored arguments. Argument offsets are relative to `source`; expressions are in evaluation order. Prefer public model types and `toDefaultMessage()` over assumptions about renderer internals.

Power-assert runtime APIs require the `ExperimentalPowerAssert` opt-in (warning level in 2.4.10). Publish the dependency and opt-in policy deliberately; test consumers compiled both with and without transformation according to the supported contract.
