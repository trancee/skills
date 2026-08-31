# Diagnostic UI state

Top-level session:
`PermissionRequired | BluetoothOff | Idle | Scanning(startedAt,count) | Connecting(device,elapsed) | Discovering(progress) | Ready(tree,generation) | Disconnecting | Failed(stage,status,cause)`.

Per attribute:
- read: `Idle | Queued(opId) | Reading(opId,startedAt) | Value(eventId,bytes,decoded) | ReadFailed(opId,cause)`
- subscription: `Idle | Subscribing(opId) | Active(subscriptionId,lastEvent) | Unsubscribing(opId) | SubscriptionFailed(opId,cause)`
- write: `Draft | Confirming(target,type,bytes) | Queued | Writing | Written | WriteFailed`

Keep prior raw value visible while a new operation progresses, but label timestamp/source/generation. Disable an action only when properties/state/queue conflict. Always provide Stop/Disconnect and expose whether it is requested versus completed.

GATT tree row content: known label (optional), full UUID, service/characteristic/descriptor instance ID, properties, permissions/security where available, current operation state, value length, raw/decoded timestamp. Use stable keys containing connection generation and instance identity.

Evidence timeline event: monotonic timestamp, generation, operation ID, stage (`submit|callback|timeout|cancel|disconnect`), Android status, attribute logical ID, byte count, queue depth. Payload/address export is opt-in and redacted by default.

Accessibility: every status/icon has text semantics; progress announces operation and target; hex can be selected/copied through an explicit redacted export action; color never carries status alone.
