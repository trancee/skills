# GATT caching, Service Changed, and EATT

Source: [Bluetooth Core 6.2 GATT caching](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/Core-62/out/en/host/generic-attribute-profile--gatt-.html).

Clients may cache handles/database definitions. If a server's GATT database never changes during usable lifetime, Service Changed should not exist. If services can be added/removed/modified or handle bindings change, Service Changed must exist and affected ranges must be indicated.

For bonded clients disconnected during a change, retain/send Service Changed state on reconnect. Unbonded caches require rediscovery or Database Hash validation according to client support. A changed Database Hash invalidates cached definitions before use.

Robust Caching requires Database Hash and Service Changed together. Track client supported features and change-aware/change-unaware state; a change-unaware robust-caching client receives Database Out Of Sync and commands/notifications are constrained until it becomes aware.

Treat handles as ephemeral cache entries, not persistent product identifiers. On invalidation, cancel outstanding transactions whose handles fall in the affected range and rediscover before access.

EATT uses multiple enhanced ATT bearers over credit-based L2CAP channels to allow concurrent transactions and reduce head-of-line blocking. Requirements/security/platform support vary. Each bearer owns MTU and transaction serialization; the single CCCD remains per client/server, not per bearer.

Concurrent bearers provide no implicit application ordering. Attach operation IDs/epochs, constrain dependent operations to one ordered path, and define conflict/atomicity when two bearers access shared attributes.
