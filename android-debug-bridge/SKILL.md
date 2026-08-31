---
name: android-debug-bridge
description: "Installs, configures, uses, and troubleshoots Android Debug Bridge (adb). Use when selecting USB, emulator, or Wi-Fi devices; pairing wireless debugging; running shell, package, and activity commands; installing APKs; copying files; forwarding ports; collecting logcat, dumpsys, bugreports, screenshots, or recordings; scripting device checks; or diagnosing unauthorized, offline, mDNS, server, and USB failures. Don't use for fastboot flashing or bootloader unlocks, Android app implementation, production device management, bypassing device authorization, destructive factory resets without explicit approval, or non-Android remote shells."
compatibility: "Uses Android SDK Platform-Tools/adb 37.0.1 documentation. Prefer the latest Platform-Tools, which are intended to remain backward compatible. Wireless pairing requires Android 11+ phones or Android 13+ TV/Wear; ADB Wi-Fi 2.0 requires Android 17+ and adb 37+. Inspector requires Python 3.11+."
metadata:
  category: "development"
  source: "https://developer.android.com/tools/adb"
  sourceVersion: "Android Developers ADB guide and Platform-Tools 37.0.1 release notes, 2026-08-31"
  createdBy: "github-copilot/gpt-5.6-sol"
  createdAt: "2026-08-31T10:08:58+02:00"
  updatedBy: "github-copilot/gpt-5.6-sol"
  updatedAt: "2026-08-31T10:08:58+02:00"
---

# Android Debug Bridge

## Step 1: Define the target and effect

1. DEFINE inspect state | run shell command | install/uninstall app | copy file | forward/reverse port | collect logs/bugreport/media | USB/wireless setup | server/mDNS/transport diagnosis | scripted device gate.
2. IDENTIFY host OS, authoritative SDK/adb path and version, target kind, exact serial/transport ID, Android/build/user/profile, boot/unlock/authorization state, package/component, local/remote paths/ports, required privilege, expected mutation, output destination/redaction, timeout, and cleanup.
3. CLASSIFY the command before execution: read-only | reversible session mutation | app/data mutation | device-wide/destructive. Ask explicit approval for destructive/device-wide effects not already requested.
4. READ the current [ADB guide](https://developer.android.com/tools/adb), installed `adb --help`, and `references/safety-troubleshooting.md` before using root/remount/reboot/sideload/testharness, package clear/uninstall, force-stop, permission changes, or device-global settings.
5. ROUTE bootloader unlock/flashing to a fastboot-specific workflow, app code changes to the relevant Android skill, and production fleet/device policy to Android Enterprise tooling.

Completion: one target, adb executable, command/effect class, expected output, timeout, and rollback/cleanup are explicit.

## Step 2: Inspect host and device state

RUN:
```bash
python3 scripts/inspect-adb.py --json
```

USE `--adb path/to/adb` when the project pins another Platform-Tools installation; use `--mdns` only while diagnosing wireless discovery. Serial values are hashed unless `--show-serials` is explicitly requested.

CONFIRM executable/version/path, server status, USB/mDNS backend, devices/transports/states, duplicates, unauthorized/offline targets, and wireless services. Resolve warnings before mutating a device.

Completion: the selected adb installation and unambiguous ready device are evidenced.

## Step 3: Install or update Platform-Tools

READ `references/architecture-version.md`.

1. PREFER Android Studio SDK Manager or `sdkmanager "platform-tools"`; otherwise use Google’s standalone Platform-Tools archive for the host OS.
2. KEEP one authoritative `platform-tools` directory on `PATH`. Compare `which`/`where`, `adb version`, Android Studio SDK path, and any distro package before blaming a device.
3. UPDATE to the latest stable Platform-Tools when protocol, USB, mDNS, pairing, install, or exit-code behavior matters; recent adb is designed to work with older Android devices.
4. VERIFY `adb version`, absolute executable path, and `adb server-status` where supported. Record vendor build suffixes separately from upstream version.
5. RESTART the host server only when version/backend/config changes require it or the server is unresponsive; killing it interrupts every adb client/device session on the host.

Completion: all commands use the intended executable/server version with no shadowing copy.

## Step 4: Establish an authorized transport

READ `references/connections.md`.

1. FOR USB, enable Developer options/USB debugging, unlock the device, connect a data-capable cable/port, and approve the workstation RSA fingerprint on-device. Never bypass authorization.
2. FOR Android 11+ wireless debugging, place host/device on a trusted same network, enable Wireless debugging, run `adb pair host:pairing-port`, and enter the one-time code at the prompt rather than in command history.
3. AFTER pairing, let secure mDNS auto-connect or run `adb connect host:connect-port` when needed; pairing and connection ports differ.
4. FOR Android 10 or lower, use the documented USB-first `adb tcpip PORT` flow only on an isolated trusted network; return to USB with `adb usb` and do not expose adbd TCP transport on untrusted networks.
5. VERIFY with `adb devices -l`. Treat `unauthorized`, `offline`, recovery, sideload, and bootloader states as distinct; `device` does not prove Android finished booting.
6. REVOKE paired hosts/USB debugging authorizations and disable wireless debugging when trust is no longer required.

Completion: one authorized transport reaches the intended device under an explicit trust boundary.

## Step 5: Select exactly one ready device

READ `references/targeting-shell.md`.

1. RUN `adb devices -l`; capture serial, transport ID, state, product/model/device, and connection type without publishing identifiers.
2. REQUIRE `-s SERIAL` or `-t TRANSPORT_ID` for every command when automation or multiple devices are possible. `-d`/`-e` are safe only when exactly one matching device exists.
3. TREAT `ANDROID_SERIAL` as process/session configuration; explicit `-s` overrides it. Log the selected target pseudonym before each mutation.
4. WAIT for the required transport state with `wait-for-...-device`, then verify readiness separately, such as `getprop sys.boot_completed == 1`, package manager availability, unlock state, or app process condition.
5. RECHECK target identity/state after reconnect, reboot, emulator restart, Wi-Fi address change, or server restart.

Completion: every command line is bound to one verified ready target and cannot fall through to another attached device.

## Step 6: Execute shell commands without quoting ambiguity

1. FOR one command, pass adb and remote arguments as an argument vector in automation; avoid composing a local shell string from untrusted data.
2. ACCOUNT for two parsers when using metacharacters: quote once for the host shell and once for the remote shell. Read the official quoting examples before pipes, redirects, globs, variables, or spaces.
3. USE noninteractive `adb -s SERIAL shell -T COMMAND...` for scripts unless a PTY is required. Keep remote exit-code/stdout/stderr behavior enabled; `shell -x` disables it.
4. USE `adb exec-out` for binary stdout such as screenshots or protobuf/raw data so PTY/newline translation cannot corrupt bytes.
5. RUN remote command `--help` (`cmd`, `am`, `pm`, `dumpsys`, `logcat`, toybox) on the target version instead of assuming flags.
6. SET finite host timeouts for commands that may wait/stream and terminate the owned process cleanly.

Completion: host/remote parsing, exit status, binary/text mode, timeout, and target are deterministic.

## Step 7: Manage apps, files, and ports deliberately

READ `references/apps-files-ports.md`.

1. CHOOSE `install`, `install-multiple`, or `install-multi-package` from artifact shape; use `-t` only for test APKs, `-r` for intended replacement, `-d` only for debuggable downgrade, and `-g` only when blanket runtime grants are part of the test.
2. VERIFY installed package/version/user with `cmd package`/`pm`; do not equate adb install success with app launch/readiness.
3. TREAT `uninstall`, `pm clear`, permission grant/revoke, force-stop, and user/profile selection as explicit app/data mutations. Name `--user` where commands can affect different users.
4. USE `push`/`pull` with explicit local and remote paths, verify checksum/size when integrity matters, and prefer app-accessible/temp paths over protected storage. Use `run-as PACKAGE` only for debuggable owned apps.
5. CREATE forwards/reverses with `--no-rebind` when replacement would be dangerous; list before/after and remove the exact mapping during cleanup.
6. KEEP forwarded host services bound/exposed only as required; port forwarding can bridge host/device trust boundaries.

Completion: package/user/data effects, file integrity/ownership, port mapping, and cleanup are verified.

## Step 8: Collect bounded diagnostics

READ `references/diagnostics.md`.

1. CLEAR logs only if the experiment requires an empty buffer and doing so is authorized; otherwise record a start timestamp and filter by buffers/tags/PID/UID/package.
2. RUN `adb logcat` with explicit format/filter and bounded duration/output. Preserve raw timestamps before postprocessing.
3. USE targeted `dumpsys SERVICE`, `cmd ...`, and `dumpsys -l` discovery before a full bugreport. Record Android build and command help/output version.
4. RUN `adb bugreport OUTPUT` for system investigations; treat the archive as sensitive because it can contain identifiers, logs, accounts, and app state.
5. CAPTURE screenshots with `exec-out screencap -p`; use bounded `screenrecord` with known limitations and pull/remove files when recording on-device.
6. REDACT/export only the evidence needed; record command, target pseudonym, UTC/monotonic boundary, exit code, and artifact checksum.

Completion: diagnostics are bounded, reproducible, minimally sensitive, and tied to the observed behavior.

## Step 9: Troubleshoot by layer

1. IF adb is missing/wrong version, fix PATH/Platform-Tools before touching devices.
2. IF no USB device appears, check cable/data mode/port, Developer options, host USB driver or Linux udev access, then `adb devices -l`; inspect host USB enumeration separately.
3. IF `unauthorized`, unlock the device, inspect/reaccept the RSA fingerprint, then revoke/re-pair only with user consent. Do not delete keys as a first step.
4. IF `offline`, wait for boot, use targeted `adb reconnect offline`, reconnect cable/network, and restart the adb server only after transport-specific checks.
5. IF Wi-Fi discovery fails, inspect `adb server-status`, `adb mdns check/services` or `track-services`, same-network/client isolation/firewall, pairing versus connect ports, and device Wireless debugging state.
6. FOR adb 37.0.1+, use `LIBADBMDNS`; release notes removed the openscreen backend and `ADB_MDNS_OPENSCREEN` no longer has effect, despite stale text in the main guide.
7. ENABLE scoped `ADB_TRACE` only for reproduction, capture the server log path from `server-status`, then remove the trace environment/restart if required.

Completion: executable, host server, USB/network transport, authorization, device boot/adbd, and command layers are isolated before reset/restart.

## Step 10: Clean up and report

1. TERMINATE streaming shell/logcat/mdns trackers and owned interactive sessions.
2. REMOVE exact forward/reverse mappings, temporary device files, test packages/data only when requested, and wireless connections/pairings no longer trusted.
3. RESTORE temporary settings/permissions/process state changed by the experiment; never leave adbd TCP mode, root, remount, or disabled verification behind.
4. COPY `assets/adb-report.md`; record host/tool/server, target/transport, commands/effects, diagnostics, artifacts/checksums, cleanup, failures, and limitations.
5. VERIFY final `adb devices -l`, mappings, process/session state, and artifact accessibility without rerunning destructive actions.

Completion: no unowned sessions/mappings/temp state remain and the exact evidence/side effects are recorded.

## Error Handling

- `adb: more than one device/emulator` -> list devices and rerun with exact `-s`/`-t`; never guess.
- `unauthorized` -> unlock and approve the displayed RSA fingerprint; verify cable/host identity and do not bypass trust.
- `offline` -> distinguish booting, USB, Wi-Fi, and stale transport; use targeted reconnect before host-wide kill-server.
- `device` but command fails -> verify boot completion, user/unlock/package/service readiness; device state only means adbd transport connected.
- Wireless pair succeeds but device absent -> use the connect port/mDNS service, not the pairing port; inspect network isolation/firewall.
- `adb shell` splits two words/metacharacters -> quote for both local and remote shells or pass argument vectors.
- Binary output is corrupt -> use `exec-out` without PTY and write bytes directly.
- Install fails -> inspect exact package-manager result, ABI/signature/version/user/storage/test-only constraints; do not loop `-r -d -g` blindly.
- `kill-server` disrupts other work -> restart once, re-enumerate, and reselect exact device; treat host server as shared.
- Command requests `testharness`, root, remount, reboot, sideload, data clear, or uninstall -> stop unless the device-wide/app-data effect is explicitly authorized.
