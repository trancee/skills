---
name: perfetto
description: "Records, instruments, visualizes, and analyzes client-side performance traces with Perfetto. Use for Android/Linux trace capture, trace_processor and PerfettoSQL queries, CPU scheduling and slice analysis, Android startup/jank/memory investigations, C++ TrackEvent SDK integration, and Perfetto tool builds. Don't use for distributed tracing backends, native Windows/macOS system capture, or unsupported causal claims from missing trace data."
compatibility: "Trace Processor prebuilts support common desktop platforms; download wrappers require Python 3 and first-run network access. System capture needs Android/adb or Linux with permitted tracefs/perf access. SDK example needs CMake and a C++17 compiler."
metadata:
  category: "testing-quality"
  source: "https://perfetto.dev/docs/"
  sourceVersion: "google/perfetto v59.1 @ 1e9c61e9844affd7dccd3d42d9ea9f3a3d10cf6d; live docs accessed 2026-11-04"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-11-04T20:10:10+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-11-04T20:10:10+01:00"
---

# Perfetto

PATHS: resolve bundled resources from the activated skill directory, not the target project's working directory. This package supplies recipes, not installed Perfetto binaries or a device connection.

## 1. Select the signal and boundary

1. RECORD the question, target process/thread, scenario, device/OS, time interval, existing trace path, and tool version. Separate the capture target from the analysis host. Preserve originals and capture configuration.
2. Existing trace -> READ [references/analysis.md](references/analysis.md). Discover recorded signals before selecting an analysis; missing scheduler, samples, heap graph, or FrameTimeline data cannot be recovered by a query.
3. New Android/Linux/Chrome capture -> READ [references/recording.md](references/recording.md). Choose only required sources and a bounded reproduction window. Obtain authorization before elevated capture, app restarts, heap dumps, or changes to device/security settings; traces can contain personal data, paths, arguments, and object contents.
4. In-app events -> READ [references/instrumentation.md](references/instrumentation.md). Prefer existing Android Trace/ATrace annotations where sufficient, C++ TrackEvents for portable application instrumentation, custom sources only for data that needs them.
5. Tool acquisition or Perfetto source changes -> READ [references/tools.md](references/tools.md). Match syntax to actual `--version`/`--help`: this baseline is v59.1, not a promise that an Android system binary or installed Python package has the same commands.
6. Keep scope explicit: built-in system probes cover Android/Linux; SDK/UI/analysis also support desktop platforms. Perfetto is client-side tracing, not an OpenTelemetry-style distributed recording service.

DONE: the required evidence, supported capture route, tool version, and sensitive/privileged boundaries are explicit.

## 2. Acquire or record usable data

1. ANALYSIS-ONLY -> leave the device unchanged. Load the supplied trace locally. Do not upload/share traces or enable network symbol retrieval without authorization.
2. CAPTURE -> copy/adapt [assets/system-trace.pbtxt](assets/system-trace.pbtxt) only for scheduler/process context. It does not record app slices, function samples, heap allocations, or Android frames. Configure those sources deliberately for those questions.
3. INSTRUMENTATION -> use [assets/CMakeLists.txt](assets/CMakeLists.txt) and [assets/track-event-smoke.cc](assets/track-event-smoke.cc) as an in-process integration probe against the selected external SDK. This probe records nested slices/counters, not system CPU time.
4. Preserve source/SDK pin, output path, recording start/stop conditions, config, and scenario markers. Finish the workload's event scopes before flushing/stopping. Retrieve the completed file before parsing it.

DONE: a real trace imports successfully and contains the target event type in the required interval, or the exact unavailable source/permission is reported; file existence alone is not capture success.

## 3. Establish coverage, then investigate

1. Load a large trace once into an owned warm session. Keep RPC local; use only the session created for this task and stop it when done. For one question, a single CLI query is sufficient.
2. RUN [assets/trace-health.sql](assets/trace-health.sql). Check time bounds, signal counts, parser errors and loss, including ring-buffer overwrite/discard counters marked `info`. Empty tables or absent statistics are not proof that the workload had no activity or no data loss.
3. DISCOVER tables, exact columns, and stdlib module documentation in the running processor before composing domain queries. Prefer stdlib objects over copied, potentially stale joins.
4. ATTRIBUTE using `utid`/`upid`; retain pid/tid and names for reporting. Use nanoseconds in the trace's clock, explicit unit conversion, and a declared region of interest. Exclude or deliberately clip unfinished intervals (`dur = -1`); distinguish instant events (`dur = 0`).
5. CPU question -> run/adapt [assets/top-cpu.sql](assets/top-cpu.sql); it clips complete on-CPU intervals to the selected window and excludes idle threads. For latency, inspect thread states and dependencies too: wall time is not CPU time. Nested slice duration sums are inclusive and can double-count work.
6. Android startup/jank/memory or sampled stacks -> follow the signal-specific routes in `references/analysis.md`. Compare like-for-like captures/builds; distinguish sampled allocations, retained managed objects, RSS, and sampled CPU stacks.
7. VERIFY the hypothesis against individual intervals/rows and the timeline. Correlation is not causal proof. Identify a distinguishing next experiment when scheduling, wakeup, lock-owner, symbol, or workload evidence is absent.

DONE: each finding has reproducible queries/row or interval evidence, units, target identity, and a stated coverage/confidence boundary.

## 4. Deliver and close

1. COPY [assets/findings.md](assets/findings.md) for a requested report, or use its fields in a short response. Separate observations, interpretations, and next experiments; cite exact SQL and timestamps rather than an unexplained metric.
2. Changes to instrumentation/config/analysis -> exercise the final path on a real trace. SDK probe expectations: one complete `SkillWork` with `Parse`/`Render` children, `QueueDepth` samples 3 then 0, and decoded `items=3`. Do not pin sleep durations or infer CPU work from the sleeps.
3. Stop owned recording/query sessions, close opened UI tabs, and remove disposable smoke outputs. Keep user traces and requested deliverables intact. Report unexercised device/platform paths explicitly.

## Error Handling

- Missing/unknown table or column -> discover the installed schema/module; check the source was captured before revising SQL. Do not return an invented zero.
- No slices -> check category/ATrace app selection, SDK registration/backend, session lifetime and flush, then loss diagnostics.
- Partial scheduler data -> inspect ftrace availability/loss and process metadata; do not identify a blocker from a sleeping state alone.
- Large trace stalls in browser -> use native Trace Processor/local RPC, not an unapproved upload; bound query output and avoid repeated parsing.
- Native stacks lack names -> obtain matching Build-ID symbols and follow symbolization guidance in `references/tools.md`; mismatched builds are not valid substitutes.
- Capture denied -> report the required source and permission; use an authorized target or in-process capture rather than weakening host/device security globally.
