# Bounded diagnostics

Logcat:
- inspect `adb logcat --help` on installed Platform-Tools/device
- select buffers, format (`threadtime`/epoch/monotonic where available), tags, PID/UID/package as supported
- record start boundary instead of clearing shared buffers by default
- bound duration/bytes and retain raw timestamps

System state:
- `adb shell dumpsys -l` lists services
- `adb shell dumpsys SERVICE [args]` narrows state
- `adb shell cmd SERVICE help` exposes version-specific commands
- capture `getprop`, package/user/AppOps/permission/process state only as required

Bugreport:
`adb -s SERIAL bugreport OUTPUT` creates a sensitive archive containing broad system/device/app evidence. Use explicit output directory, sufficient disk/time, checksum, access control, and redaction/retention policy.

Media:
- screenshot: `adb -s SERIAL exec-out screencap -p` to a binary-safe host writer
- recording: `screenrecord` is bounded/limited and omits some protected content/audio; inspect target help, stop cleanly, pull, then remove remote temp file

Performance/profiling uses dedicated tools such as Perfetto/Studio Profiler; Platform-Tools no longer includes systrace. ART profile retrieval, sqlite, JDWP, and device-policy commands require exact app/device ownership and version-specific help.

Every artifact records target pseudonym, Android/build, UTC and monotonic boundary, exact command/filters, exit status, size/checksum, redactions, and limitations.
