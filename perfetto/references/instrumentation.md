# Instrument applications with real TrackEvents

Sources: [Tracing SDK](https://perfetto.dev/docs/instrumentation/tracing-sdk), [TrackEvents](https://perfetto.dev/docs/instrumentation/track-events), [v59.1 SDK example](https://github.com/google/perfetto/blob/v59.1/examples/sdk/example.cc), [example build](https://github.com/google/perfetto/blob/v59.1/examples/sdk/CMakeLists.txt), [Android ATrace](https://perfetto.dev/docs/getting-started/atrace).

## 1. Select the integration

- Android-only slices -> keep `android.os.Trace`/NDK `ATrace_*` when sufficient. Pair begin/end on the same thread, normally in `finally`/RAII; asynchronous operations need the appropriate async API and stable matching cookie. Enable app/categories in the actual capture config.
- C++ application events -> use the self-contained `perfetto.h`/`perfetto.cc` amalgamated SDK from one reviewed release. Require C++17; do not combine header/source files from different versions.
- In-process backend -> application owns the service/session and can read its own trace without OS tracing privileges. It contains no scheduler data unless separately captured/merged correctly.
- System backend -> producers connect to reachable `traced`; the external consumer controls capture. Do not attempt to read other processes' trace data from a producer. Initialize only intended backends.
- Custom strongly typed data -> follow [custom sources](https://perfetto.dev/docs/instrumentation/tracing-sdk#custom-data-sources) and importer/extension requirements, not arbitrary fields that the UI will supposedly understand. Rust -> follow the separate [Rust SDK](https://perfetto.dev/docs/getting-started/rust-sdk); C++ macros/build commands are not Rust integration.

## 2. Exercise an in-process integration

1. Download `perfetto-cpp-sdk-src.zip` from the selected [release](https://github.com/google/perfetto/releases/tag/v59.1), verify provenance, and extract outside the skill. Point `PERFETTO_SDK_DIR` at the directory containing both SDK files.
2. Copy `assets/CMakeLists.txt` and `assets/track-event-smoke.cc` into a disposable consumer directory. Build and record:

```bash
cmake -S probe -B probe-build \
  -DPERFETTO_SDK_DIR="$PERFETTO_SDK_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build probe-build --parallel 2
./probe-build/perfetto-skill-probe demo.pftrace
```

Choose a new output file: the example deliberately truncates the named output. Windows executable paths differ; the build asset supplies MSVC bigobj/conformance, WinSock, and Windows macro guards. Android links the logging library; Linux/other toolchains link thread/dl requirements as appropriate.

3. Load `demo.pftrace` into Trace Processor/UI. Require one complete `SkillWork` with children `Parse`/`Render` on the same track, `items=3` on `Parse`, and `QueueDepth` samples 3 then 0. Check nested event `parent_id`/depth rather than merely file size. Sleeps make the demo visible; they do not model CPU processing or measure instrumentation overhead.
4. Missing events -> inspect source/category registration, backend selection, session activation and event scopes before stopping. Keep the final recorded bytes and decoded event proof for the chosen SDK/tool versions.

## 3. Preserve lifetime and session invariants in real code

1. Define categories in a shared header and emit `PERFETTO_TRACK_EVENT_STATIC_STORAGE()` in exactly one implementation unit for that registry. Initialize `Tracing` and register `TrackEvent` before recording.
2. Select data source `track_event`; use `TrackEventConfig` with disabled `*` and explicitly enabled categories for bounded output. Exact enabled matches take precedence over wildcard disable. Do not assume debug/slow category defaults match C API or another version.
3. Scoped `TRACE_EVENT` ends at the surrounding C++ block exit. Manual BEGIN/END shares a per-track stack: balanced thread-local nesting is required. Work spanning functions/threads should use an explicit stable track and matched begin/end/flows; a flow links events but does not itself measure execution time.
4. Prefer static event/category names. For truly dynamic names, pass a temporary `perfetto::DynamicString{...}` whose source survives evaluation. `StaticString` promises stable lifetime and immutable contents; using it for reused buffers can silently corrupt traces. Record needed arguments inside the event callback, which may run once per active session; do not consume/move state or introduce workload side effects there.
5. Use numeric `TRACE_COUNTER` values on a consistent counter track/unit. Counter samples are state observations, not intervals or allocation records. Avoid sensitive/high-cardinality names and payloads unless required and authorized.
6. End event scopes, flush TrackEvents, stop the session, then read the finished trace. The bundled synchronous probe uses `StartBlocking`, `StopBlocking`, and `ReadTraceBlocking`. Long production sessions can stream via `Setup(config, fd)` under the documented ownership/lifetime rules rather than buffering the whole trace in RAM. Handle write/session errors explicitly.

DONE: a captured trace decodes the intended event nesting, annotations and counters, and the real instrumentation preserves workload semantics and bounded overhead.
