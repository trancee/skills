# GATT failure verification

Deterministic tests:
- non-success + connected never advances
- success + disconnected retires correctly
- callback for old GATT/epoch cannot close/advance current attempt
- null/throw/connect timeout/cancel/disconnect callback/deadline close exactly once
- discovery submission false/callback failure are not connection failures
- one retry scheduled despite callback-timeout race
- retry waits for cleanup and creates fresh GATT
- permanent/user-action statuses suppress retry
- capped backoff+jitter/budget and cancellation under virtual time
- scheduler shutdown/recreation never schedules on a terminated executor

Compile/static matrix:
- target API 31+ permission branches
- API 37 settings + explicit Executor and lower-SDK connection branch
- API 37.2 thresholds only with actual full/minor SDK
- no hidden `refresh`, no programmatic adapter toggle, no address logs

Real matrix:
- Android 12–17 representative OEMs and known-good/failing peripherals
- fresh/stale/non-connectable scan, direct/auto, first/reconnect, foreground/background
- peer absent/range/RF contention/max connections/reset
- bond/key loss/pairing reject/security-required characteristic
- rapid tap/cancel, adapter toggle, permission revoke, process kill
- same phone with another peer/client and same peer with another phone

Capture reproduction counts, callback timeline, logcat/dumpsys/bugreport, HCI/peer trace, and before/after intervention evidence. Do not claim root cause from status frequency alone.
