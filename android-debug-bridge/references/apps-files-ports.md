# Apps, files, and port mappings

Install selection:
- one APK: `install`
- split APK set for one app: `install-multiple`
- several packages atomically: `install-multi-package`
- `-r` replace, `-t` test-only, `-d` debuggable downgrade, `-g` grant all runtime permissions—each changes semantics and must be intentional

Verify package with target user through `adb shell cmd package`/`pm`. Name `--user USER_ID` for install-existing, clear, enable/disable, grant/revoke, force-stop, and component operations where supported. `uninstall` removes app/data; `uninstall -k` retains data/cache. `pm clear` is destructive.

Use `push [--sync]` and `pull [-a]` with explicit paths. Verify size/checksum for test fixtures/artifacts. Protected app data requires a debuggable owned package and `run-as`; adb shell/root is not a production data-access bypass. Use `exec-out run-as PACKAGE ...` carefully for binary output.

Port mappings:
```text
adb -s SERIAL forward --list
adb -s SERIAL forward --no-rebind tcp:HOST_PORT tcp:DEVICE_PORT
adb -s SERIAL forward --remove tcp:HOST_PORT
adb -s SERIAL reverse --list
adb -s SERIAL reverse --no-rebind tcp:DEVICE_PORT tcp:HOST_PORT
adb -s SERIAL reverse --remove tcp:DEVICE_PORT
```

Use `tcp:0` when adb should allocate a free port and capture the returned port. List/verify mappings and remove exact ownership. Avoid `--remove-all` on shared devices/hosts. A forward/reverse can expose services across host/device trust boundaries; secure the listening service independently.
