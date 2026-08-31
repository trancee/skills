# Connection-attempt lifecycle

State:
`Idle -> Preparing -> Connecting(attempt,gatt,deadline) -> Connected -> Discovering -> Ready -> Retiring -> Closed -> RetryWait/Failed`.

Invariants:
- one owner controls one attempt ID/epoch/GATT
- attempt state installs before `connectGatt` can callback
- callbacks match their `gatt` argument and epoch before mutation
- status precedes newState
- exactly one terminal path retires and closes
- replacement attempt starts only after prior cleanup
- discovered Android objects never cross epochs

API 37 settings separate:
- `setAutoConnectEnabled`: direct false versus automatic connection true
- `setOpportunisticEnabled`: client does not hold the shared GATT connection and disconnects when no other clients remain
- `setAutomaticMtuEnabled`: defaults true
- transport: set LE for intended BLE path
- RSSI/pathloss thresholds: API 37.2 preferences for auto-connect and controller-dependent, absent from 37.0/37.1 public stubs

Use an explicit serial Executor with the API 37 `connectGatt(settings, executor, callback)`. Older branches use explicit LE transport where available.

On callback non-success: retire immediately, fail pending work, close exact callback GATT, compare-and-clear owner field, then classify/retry. On user disconnect from connected: retire work, call disconnect, await disconnected only to a bounded deadline, then close. On connecting timeout/cancel: retire and close without indefinite callback wait.

Service discovery begins from verified success with no generic sleep. Treat `discoverServices()==false`, callback status failure, and service-changed as their own stages.
