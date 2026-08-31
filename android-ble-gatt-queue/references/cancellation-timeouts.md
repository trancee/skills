# Cancellation, timeout, and reset

Separate two completions:
- caller reply: follows caller cancellation and may stop being observable
- internal transport completion: remains owned by queue until Android callback or epoch reset

Create caller reply with caller Job ownership or explicit cancellation hook. If cancelled while queued, worker skips it. If cancelled in-flight, do not submit the next request: Android exposes no per-request cancellation, so retain/await internal completion and discard outward result.

A timeout means the callback contract is no longer trustworthy. Safest policy:
1. atomically retire epoch/in-flight ID
2. fail timed-out and queued replies with typed timeout/reset cause
3. close/drain request channel and event stream
4. disconnect/close GATT exactly once
5. ignore late callbacks by old instance/epoch
6. reconnect/rediscover/resubscribe through outer owner if policy allows

Removing a deferred/map entry then advancing can overlap the still-running Android request and misattribute its late callback.

Race tests cover cancellation before enqueue, queued, between in-flight install/submission, after acceptance, simultaneous callback/cancel, callback at timeout boundary, owner shutdown, permission loss, disconnect, and reconnect. Completion/CAS must be idempotent.

Timeout values are per operation and device behavior, not one magic constant. Diagnostic result records operation ID/type/target/epoch, elapsed time, submission result, last connection state, and GATT status without payload secrets.
