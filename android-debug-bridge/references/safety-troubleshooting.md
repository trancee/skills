# Safety and troubleshooting

Effect gates:
- read-only: version/devices/getprop/logcat/dumpsys/list/query
- reversible session: forward/reverse, force-stop/start, temporary settings/permissions, connect/disconnect transport
- app/data mutation: install/uninstall, `pm clear`, grant/revoke, push over existing file, user/profile changes
- device-wide/destructive: reboot modes, sideload, root/unroot, remount/verity, testharness factory reset, global settings, adb keys/authorizations

Execute destructive/device-wide commands only when the user explicitly requested the exact effect and target. `adb shell cmd testharness enable` factory-resets the device and changes security/system settings; never use it as generic cleanup. `adb root`, remount, disable-verity, reboot bootloader/recovery, sideload, and production/user-device policy changes are out of routine app debugging.

Troubleshooting order:
1. executable/PATH/version and shared server status
2. host USB/network visibility/backend/firewall
3. RSA/pairing trust and target selector
4. adbd transport state and Android boot/user state
5. remote command/package/privilege
6. only then targeted reconnect or server restart

`kill-server` is host-wide and interrupts IDEs/scripts/all devices. Prefer `adb reconnect offline`, cable/network reconnect, or specific `disconnect ENDPOINT`. After restart, enumerate and select again.

Wireless: distinguish pair port from connect port, paired trust from active connection, and mDNS discovery from direct `adb connect`. For 37.0.1+, openscreen is removed and `ADB_MDNS_OPENSCREEN` is ignored.

For reproducible host bugs, set scoped `ADB_TRACE` categories/levels, restart only if required, reproduce once, collect the server log from `server-status`, then unset trace and restore normal server state.
