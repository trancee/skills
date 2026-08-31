# Device targeting and shell execution

Target selectors:
- `-s SERIAL`: exact device/emulator/network endpoint; overrides `ANDROID_SERIAL`
- `-t TRANSPORT_ID`: exact current transport from `devices -l`
- `-d`: sole USB device only
- `-e`: sole TCP/IP/emulator transport only

Automation always selects explicitly and revalidates after reconnect/reboot. Hash serials in logs. `wait-for-device` waits for transport, not Android boot; follow with `adb -s SERIAL shell getprop sys.boot_completed` and any required package/user/unlock readiness.

Shell command has host-shell and device-shell parsing. Prefer a process argument vector. For an interactive host shell, quote twice when remote quotes/metacharacters must survive, as the official example does:
```bash
adb -s SERIAL shell setprop key "'two words'"
```

Use `shell -T` for noninteractive text scripting and default remote exit-code separation. `shell -x` disables remote exit codes and stdout/stderr separation, so avoid it in verification scripts. Use PTY only for interactive commands.

Use `exec-out` for raw binary stdout:
```bash
adb -s SERIAL exec-out screencap -p
```

Never interpolate untrusted package/path/intent/SQL text into a remote shell string. Validate allowlists and use direct arguments; when a remote pipeline is required, make both parse layers explicit and inspect final argv/command in tests.
