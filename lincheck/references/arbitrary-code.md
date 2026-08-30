# Testing arbitrary concurrent code

Source: [Testing arbitrary code](https://kotlinlang.org/docs/lincheck-testing-arbitrary-code.html).

Lincheck 3.x tests an explicit concurrent program with:
```kotlin
@Test
fun counter() = Lincheck.runConcurrentTest {
    var counter = 0
    val first = thread { counter++ }
    val second = thread { counter++ }
    first.join()
    second.join()
    assertEquals(2, counter)
}
```

The optional invocation count repeats exploration. Use the smallest count that reliably reproduces the issue.

## Design rules

- create fresh state for each test invocation
- create/join all JVM threads inside the block
- assert an observable safety/postcondition or allow the intended deadlock/stall to be detected
- avoid sleeps, wall-clock assertions, I/O, logging, executors with unrelated workers, and global mutable fixtures
- keep operations small enough for useful switch-point traces
- ensure cleanup cannot leak threads after success/failure

Use this API when the exact thread choreography matters: compound actions, lock ordering, check-then-act races, unsafe publication, or arbitrary code not naturally represented as data-structure operations.

A failure report lists threads, operations, reads/writes/switches, and assertion/exception/stall. Read from the first shared access whose observed value differs from the required invariant. Logging can change scheduling; use Lincheck's trace and IntelliJ plugin instead.

Passing means no counterexample was found within explored schedules. It does not establish Java Memory Model correctness or liveness beyond configured checks.
