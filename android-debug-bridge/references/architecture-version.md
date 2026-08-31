# ADB architecture and version ownership

ADB has a host client, one host server (normally localhost TCP 5037), and a device daemon (`adbd`). All host clients share the server, so `kill-server`, server environment, keys, backends, and version affect concurrent Android Studio/scripts/devices.

Install Platform-Tools with Android Studio SDK Manager or `sdkmanager "platform-tools"`; standalone archives must come from Google. Prefer latest stable Platform-Tools because they are intended to be backward compatible with older Android releases.

Resolve one executable:
- Linux/macOS: `command -v adb`, `adb version`, SDK root/platform-tools path
- Windows: `where adb`, `adb version`
- compare Android Studio’s configured SDK with terminal PATH

`adb version` reports protocol version, package version/build, executable path, and host OS. `adb server-status` (recent versions) reports executable/log/key paths, USB/mDNS backend, trace, and burst mode. A distro build suffix may differ from Google packaging; record it.

ADB 37 changes:
- adb 37.0.0 and Android 17 introduce Wi-Fi 2.0 automatic trusted-network reconnection
- 37.0.1 removes the openscreen mDNS backend; `ADB_MDNS_OPENSCREEN` no longer has effect and `LIBADBMDNS` is the only backend
- `ADB_TRACE` accepts per-category log levels in 37.0.1

The main ADB guide still contains older openscreen recovery text. Prefer the current Platform-Tools release note for the installed version.
