# Coroutine and blocking-I/O lifecycle

Java blocking Bluetooth calls are not made cancellable by `withContext(Dispatchers.IO)` or `withTimeout` alone. Cancellation must close the exact `BluetoothServerSocket`/`BluetoothSocket`, which Android documents as thread-safe and immediately aborting ongoing operations.

Use one parent Job per listener/connection and child reader/writer/parser jobs. Install close cleanup before suspension/blocking execution can outlive ownership. Make `closeOnce(cause)` atomic/idempotent:
1. select first terminal cause
2. mark closing so no new work enters
3. close listener/connected socket
4. close bounded channels
5. cancel/join child jobs without self-join
6. publish one terminal outcome

Expected `IOException` caused by deliberate close is cleanup evidence, not a replacement failure. Preserve timeout/cancellation as primary cause; retain unexpected close errors as suppressed/diagnostic data.

Use `Dispatchers.IO` or a dedicated bounded executor. Unbounded one-thread-per-connection designs can exhaust memory. Keep one read owner and one write serializer per socket; socket thread safety does not make application framing safe under concurrent writers.

If adapting to `suspendCancellableCoroutine`, wire `invokeOnCancellation { socket.close() }`, handle the callback/close race exactly once, and join the blocking worker. Prefer structured `withContext` plus an owner that closes on cancellation over detached `GlobalScope` work.
