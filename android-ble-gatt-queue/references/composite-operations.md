# Composite operations and unsolicited events

## Subscription

A subscription is one public operation with two internal steps:
1. call `setCharacteristicNotification(characteristic, enabled)` for local routing; fail synchronously if false
2. write CCCD (`0x2902`) using API 33+ `writeDescriptor` with enable-notify, enable-indicate, or disable bytes; await `onDescriptorWrite`

Choose notify versus indicate from characteristic properties/product contract. Mark ready only after descriptor success. If CCCD step fails, disable local routing where possible. On reconnect/service change, rediscover objects and repeat.

`onCharacteristicChanged` is unsolicited. Copy bytes, tag epoch/characteristic instance/time/sequence, and `tryEmit`/`trySend` to a bounded stream. Define overflow: drop-oldest with metric for live telemetry, disconnect/fail for lossless protocols, or backpressure at application protocol—not callback-thread suspension.

## Reliable write

Treat `beginReliableWrite`, each write + `onCharacteristicWrite` value verification, `executeReliableWrite`/`abortReliableWrite`, and `onReliableWriteCompleted` as one exclusive transaction. No ordinary operation interleaves. Abort on mismatch, cancellation before execute, status failure, or timeout; reset connection if final state is uncertain.

## Discovery/configuration

Service discovery, optional MTU, characteristic lookup, and subscriptions form an explicit readiness workflow. Await real callbacks; fixed sleeps do not prove readiness. Service Changed terminates readiness and invalidates queued discovered objects.
