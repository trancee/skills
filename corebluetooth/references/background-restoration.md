# Background execution and restoration

Current Core Bluetooth symbol pages override the archived [Core Bluetooth Background Processing for iOS Apps](https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/CoreBluetooth_concepts/CoreBluetoothBackgroundProcessingForIOSApps/PerformingTasksWhileYourAppIsInTheBackground.html) for API signatures and current platform behavior.

Declare `UIBackgroundModes` value `bluetooth-central` and/or `bluetooth-peripheral` only when the corresponding user-visible workflow requires it. The system wakes an app for relevant delegate events; process the event and return promptly. Background execution is constrained and may be throttled or terminated.

Background central behavior:
- scan with one or more service UUIDs; current scan documentation requires explicit services
- scan options have no effect; duplicate discoveries are coalesced
- discovery may be slower when scanning apps are in background
- connected peripheral delegate events can wake the app with central mode

Background peripheral behavior:
- local name is not advertised
- service UUIDs move to overflow and are discoverable by iOS peers explicitly scanning for them
- advertising may slow
- `bluetooth-peripheral` allows wake for reads, writes, and subscriptions

State restoration is opt-in and distinct from ordinary suspension:
1. generate one stable, distinct UID per manager and persist it
2. pass `CBCentralManagerOptionRestoreIdentifierKey` or `CBPeripheralManagerOptionRestoreIdentifierKey` every time that manager is created
3. implement the matching `willRestoreState`
4. retain restored peripherals/services and reassign peripheral delegates
5. inspect restored scan options, connections, discovered attributes, published services, advertising, and subscriptions
6. reconcile idempotently from actual state; resume only missing steps

Scene-based apps cannot use app-delegate launch options to obtain manager identifiers because scene launch options are `nil`; persist UIDs independently. Missing restoration dictionary entries require application-owned recovery. User force quit and unsupported platform contexts are terminal product scenarios; test them explicitly rather than promising relaunch.

The Core Bluetooth root documentation states that iOS 26 Live Activities can grant an instantiated `CBManager` the same background privileges it has in foreground. Use this only for a legitimate Live Activity and recheck current ActivityKit, App Review, energy, and Core Bluetooth requirements.
