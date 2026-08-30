# Declarative concurrent data-structure tests

Source: [How to test data structures](https://kotlinlang.org/docs/lincheck-how-to-test-data-structures.html).

```kotlin
class StackTest {
    private val stack = ConcurrentStack<Int>()

    @Operation
    fun push(value: Int) = stack.push(value)

    @Operation
    fun pop(): Int? = stack.pop()

    @Test
    fun modelChecking() = ModelCheckingOptions().check(this::class)
}
```

Lincheck generates initial, parallel, and post operations, executes schedules, and verifies observable results. Linearizability is default.

## Operation contract

Expose every concurrent method necessary to distinguish valid histories. Return actual results and let expected exceptions remain observable. Avoid helper operations that mutate hidden state outside the subject.

Execution options:
- `nonParallelGroup`: operations in one group never overlap each other
- `runOnce`: at most once per invocation
- `blocking`: intentional blocking; relevant to progress checks
- `cancellableOnSuspension`: suspend operation may be cancelled while suspended
- `promptCancellation`: cancellation may win after resume before result processing

Each option removes/adds histories. Set only from production semantics.

## Argument generation

Use class/parameter `@Param` with built-in or custom generators. Small collision-heavy domains expose races better than full ranges: repeated map keys, empty/full capacities, boundary numbers, duplicate values. Cover special sentinels/null separately when allowed.

## Custom scenarios

Use `addCustomScenario` with `initial`, `parallel/thread`, and `post` actors to preserve a known regression. Keep random scenarios too; one custom history cannot cover the algorithm.
