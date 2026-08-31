# Verification matrix

Unit/state-machine tests with fake delegate events:
- manager states and authorization transitions
- scan start/replacement/stop, duplicate discovery, selection, and retained peripheral
- connect success/failure/app timeout/cancel/disconnect/reconnect generations
- ordered partial/full discovery and `didModifyServices` invalidation
- read versus notification routing through `didUpdateValueFor`
- with-response write completion/error; without-response capacity false/ready resume
- maximum-write chunk boundaries, cancellation, timeout, and late callback rejection
- set-notify success/error/disable and event stream lifetime
- local service add/advertising callbacks
- ATT read offsets and exact one response
- multi-request write validation, atomic application, and first-request response
- `updateValue == false`, same-chunk retry, multi-central limits, unsubscribe
- restoration dictionaries with complete, partial, missing, and duplicate state

Compile/test each supported Apple platform and lowest deployment target. Availability guards must compile at the boundary; test advertising rejection/absence for watchOS, tvOS, and visionOS targets rather than assuming shared declarations are usable.

Real-device matrix requires at least two Bluetooth-capable devices/roles. Exercise Bluetooth off/on/reset, authorization denied, foreground/background/suspension, screen lock, system termination/restoration, force quit, peer power/range loss, malformed/long values, queue saturation, and reconnect. The iOS simulator and mocks do not prove radio, background scheduling, restoration, or peer behavior.

Capture PacketLogger/controller/over-air traces when advertisement contents, ATT ordering/errors, notification delivery, L2CAP framing, or peer behavior is disputed. Redact identifiers and payload secrets. Report device model, OS, role, app state, peer firmware, timing, expected result, and observed callbacks.
