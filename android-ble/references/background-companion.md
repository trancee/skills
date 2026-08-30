# Background and process lifecycle

Source: [Communicate in the background](https://developer.android.com/develop/connectivity/bluetooth/ble/background).

Background BLE is a process-lifecycle problem:
- callback scan/active GATT need the app process alive
- process death closes connections and invalidates callbacks/platform objects
- PendingIntent scan can start a dead process for filtered matches
- Worker/job suits finite work and may be interrupted
- `connectedDevice` FGS suits user-visible long transfer/connection when start restrictions permit
- Companion Device association/presence/`CompanionDeviceService` suits long-lived companion devices

Choose one path from user intent and duration. Do not combine WorkManager, repeating alarms, restart receivers, and an FGS into competing owners.

Persist only logical state: associated device/application ID, transfer checkpoint, desired subscription, retry deadline, and user intent. Never persist `BluetoothGatt`, `BluetoothDevice` object identity, discovered characteristic objects, callbacks, or runtime handles.

On restart: recheck permission/adapter/association, recreate owner/epoch, find/connect, rediscover, validate services, rewrite CCCDs, resume idempotently. Treat notifications during absence according to product data-loss semantics.

Start FGS while visible or under an explicit exemption, call `startForeground` within required deadline, show accurate ongoing notification/actions, and stop when work/user intent ends. Permission revocation/user stop is terminal until new intent.
