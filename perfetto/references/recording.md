# Record the evidence needed

Sources: [system tracing](https://perfetto.dev/docs/getting-started/system-tracing), [Linux cookbook](https://perfetto.dev/docs/getting-started/linux-cookbook), [config](https://perfetto.dev/docs/concepts/config), [buffers/loss](https://perfetto.dev/docs/concepts/buffers), [v59.1 scheduler example](https://github.com/google/perfetto/blob/v59.1/test/configs/scheduling.cfg).

## 1. Choose sources and a bounded window

1. SELECT the reproduction/target and required signal. The bundled `assets/system-trace.pbtxt` captures five seconds of scheduling plus process/thread metadata with a 32 MiB central buffer. Copy it to the capture workspace before editing; kernel event availability varies by target.
2. Use `linux.ftrace` scheduler events plus `linux.process_stats` for attribution. App annotations require ATrace config or SDK `track_event`; sampling, heaps, Android frames and logcat need separate sources. Existence of a trace file does not establish that a requested source started.
3. Map sources to valid zero-based `target_buffer` indices. `DISCARD` preserves early data but drops new packets when full; `RING_BUFFER` retains the tail and overwrites earlier data. Separate high-rate ftrace from metadata buffers when loss would erase attribution. Size for observed event rate, not elapsed time alone.
4. Long traces -> use bounded `write_into_file` streaming with explicit duration/file limits and suitable write period. Kernel per-CPU, producer shared-memory and central buffers are separate loss points; enlarging the central buffer cannot fix all loss. Limit chatty sources before increasing capture overhead.

## 2. Android capture through the selected device

Use existing authorized USB debugging. Select a connected serial explicitly; do not switch to a different device if recording fails. Inspect the on-device `perfetto --help` and `--query` capabilities. Modern Android ships the service; older targets can require upstream's helper/sideloading workflow.

```bash
adb devices -l
adb -s "$SERIAL" shell perfetto --query
adb -s "$SERIAL" shell perfetto --txt -c - \
  -o /data/misc/perfetto-traces/skill-scheduling.pftrace < system-trace.pbtxt
adb -s "$SERIAL" pull /data/misc/perfetto-traces/skill-scheduling.pftrace ./scheduling.pftrace
```

Choose a new output filename to avoid clobbering an existing capture. The foreground recording stops after the config duration; reproduce concurrently on the device. Text config needs `--txt`, otherwise `-c` expects serialized TraceConfig protobuf. Do not use `--txt-lossy` to hide unknown fields; the source may silently remain disabled.

For scripted startup synchronization, inspect support for `--background-wait` (`-D`), which acknowledges source startup before returning. Preserve its printed owned PID and the duration limit; stop only that session gracefully if needed and wait for completed output before pulling. Disconnect/forced termination can lose buffered events. Prefer this bounded lifecycle over detached-mode keys or killing all tracing daemons.

The official [record_android_trace helper](https://github.com/google/perfetto/blob/v59.1/tools/record_android_trace) can capture, pull, and open the UI; inspect its own `--help` for serial, config and `--no-open` options. Do not mix helper flags with on-device client flags. Enable ATrace categories and the specific app package only when its slices are needed.

## 3. Linux or Chrome capture

Linux: use the selected `tracebox` with the copied config:

```bash
./tracebox --txt -c system-trace.pbtxt -o scheduling.pftrace
```

ftrace/perf access may require an authorized privileged invocation. Do not recursively chown tracefs, lower `perf_event_paranoid`/`kptr_restrict`, or disable security policies as routine setup. Check kernel/config/source support and use an approved environment instead. In-process SDK events need neither ftrace nor root; they are not substitutes for scheduler evidence.

Chrome: follow [Chrome tracing](https://perfetto.dev/docs/getting-started/chrome-tracing) and the UI recording page; select the browser target/categories/duration, reproduce, stop and inspect the imported trace. OS-level Windows/macOS probes are not provided by Perfetto; analyze a supported external recording format when appropriate.

## 4. Select deeper profiling deliberately

| Question | Required route | Evidence limit |
|---|---|---|
| On-CPU functions | [CPU profiling](https://perfetto.dev/docs/getting-started/cpu-profiling), `linux.perf` and matching symbols | Samples are statistical, not every function call |
| Native allocations | [heapprofd](https://perfetto.dev/docs/data-sources/native-heap-profiler) | Sampling/attach eligibility and overhead; allocation churn != live heap |
| Managed retention | [ART heap graph](https://perfetto.dev/docs/data-sources/java-heap-profiler) | Object snapshot/retaining paths, not all historical allocations |
| Frame deadlines | [FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline) plus app/system context | Requires supported Android/source data, not slice duration alone |

Use the source's supported app debuggable/profileable rules; do not promise rootless access to arbitrary production apps. Heap captures can pause workloads and contain highly sensitive data. Linux `blocked_function` is generally not supplied like Android's blocked-reason event; use the [Linux blockage recipe](https://perfetto.dev/docs/getting-started/linux-cookbook) when that attribution is required.

DONE: import the finished trace, locate the scenario/target, check required event coverage and loss stats. Empty sources -> fix config/eligibility/startup first, not the query.
