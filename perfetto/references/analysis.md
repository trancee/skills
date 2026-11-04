# Query, visualize, and validate findings

Sources: [SQL concepts](https://perfetto.dev/docs/analysis/perfetto-sql-getting-started), [stdlib](https://perfetto.dev/docs/analysis/stdlib-docs), [CLI cookbook](https://perfetto.dev/docs/getting-started/command-line-analysis), [Android cookbook](https://perfetto.dev/docs/getting-started/android-trace-analysis), [UI](https://perfetto.dev/docs/visualization/perfetto-ui). Commands below use a native/wrapper executable named `trace_processor`; substitute the selected path, e.g. `trace_processor_shell` from a release archive.

## 1. Load once and inspect coverage

For one-off analysis:

```bash
trace_processor query --format csv -f trace-health.sql trace.pftrace
```

Copy `assets/trace-health.sql` from the skill or pass its resolved package path. For iterative work on POSIX, use a unique owned session name:

```bash
trace_processor server unix --name investigation --daemonize trace.pftrace
trace_processor query --remote investigation --format csv -f trace-health.sql
# Run all subsequent queries against that session.
trace_processor server kill investigation
```

The `unix` session mode is POSIX-specific. Windows/other clients -> use one local Python `TraceProcessor` context or supported local RPC; check installed help. Configure trace-loading flags on the server invocation, not `query --remote`. Do not reuse/kill another user's named session. CSV avoids agent-mode Markdown truncation and is suitable for machine parsing; bound exploratory rows regardless.

Health checks include trace bounds, signals and anomalous nonzero stats. A clean `data_loss` severity query alone misses central-buffer overwrite marked `info`. Validate that the selected interval survives buffering and contains the target; absent counters can also mean the source/config is missing. Incomplete slices use `dur=-1`; instant events use zero.

## 2. Discover the installed schema

```sql
SELECT name FROM perfetto_tables ORDER BY name;
SELECT * FROM slice LIMIT 0;
SELECT qualified_name, object_type, short_description
FROM __intrinsic_stdlib_objects
WHERE exposed = 1 AND regexp('startup|frame|memory', summary, 'i')
LIMIT 20;
```

Read the object's `summary`, include its module, then inspect its exact columns. These discovery tables are version-dependent; if absent, use that version's schema/stdlib docs. Do not repair a query by assuming a similarly named column has the same semantics.

```sql
INCLUDE PERFETTO MODULE slices.with_context;
SELECT id, ts, dur, name, thread_name, process_name, utid, upid
FROM thread_slice
WHERE dur >= 0
ORDER BY dur DESC LIMIT 20;
```

Use `process_slice` for process tracks and `thread_or_process_slice` for both. Joining every slice through `thread_track` drops async/process tracks. Query `args` by `arg_set_id` (or documented extraction functions) for annotations, not string parsing of display labels.

## 3. Attribute time correctly

1. Fix the region of interest `[start_ns,end_ns)` in the trace clock; retain absolute trace timestamps for reproducibility and convert durations with `/1e6` for milliseconds. SQL uses nanoseconds regardless of a UI's display units. Clock alignment matters when combining traces/machines.
2. Use `assets/top-cpu.sql` for on-CPU totals. It clips complete scheduler intervals crossing the window and excludes idle threads; unfinished final rows are omitted and can undercount the tail. Group by `utid`/`upid`, not recyclable OS identifiers or repeated names.
3. For latency, inspect `thread_state`, wakeups and relevant caller/dependency intervals. Runnable time is scheduler wait, running time is on-CPU, sleeping/blocked states are not by themselves a named lock or cause. Several CPUs can run concurrently; summed CPU milliseconds can exceed elapsed milliseconds.
4. Slice `dur` is inclusive wall time, usually including child slices and descheduling. Summing parent and child work double-counts; either choose the relevant level, union intervals, or use documented self-time/overlap modules. For windowed state/counter averages, use interval intersection and duration weighting, not a naive average of sample rows.
5. Empty query -> check trace type, target identity, interval, modules and source eligibility. A missing callstack/blocked reason cannot be reconstructed by correlating neighboring names.

## 4. Route Android and profile questions by recorded data

| Question | Discover/include module | Validate before interpreting |
|---|---|---|
| Startup | `android.startup.startups` | Startup instance, process, cold/warm conditions and captured launch window |
| Jank | `android.frames.timeline` | App vs compositor deadlines, actual FrameTimeline data, UI/render-thread dependencies |
| Binder or ANR | Search stdlib for binder/ANR objects; `android.anrs` where available | Server/caller correspondence and surrounding thread states, not one long slice |
| CPU samples | `stacks.cpu_profiling` | Sampling coverage, sample counts, resolved symbols; self vs cumulative counts |
| RSS/swap | Discover `linux.memory.process` / Android memory process modules | Measured fields, units and polling; RSS alone is not a heap leak |
| Native allocations | `android.memory.heap_profile.summary_tree` where available | Allocation/free deltas, sampling interval and live-vs-total interpretation |
| Java retention | `android.memory.heap_graph.dominator_tree` | Dump timestamp/process, reachability, retained-vs-shallow bytes and actual retaining path |

Use [memory case study](https://perfetto.dev/docs/case-studies/memory) and source-specific docs for the required next capture. A rising counter or one large object is insufficient leak proof; compare equivalent workload/GC states and inspect ownership/retainers.

## 5. Visual and programmatic verification

- UI: open the local file; search the target, expand thread tracks, select a slice/state, use `F` to fit and W/S/A/D to zoom/pan. Query (SQL) supports Ctrl/Cmd+Enter. Include `id`, `ts`, `dur`, `track_id` when linking query results back to intervals; use current UI controls rather than assuming old screenshots match.
- Browser-local processing does not authorize Share/upload or enabling remote extension/symbol servers. Large traces -> native local processor/RPC instead of uploading to a third party.
- Python automation -> install/pin `perfetto` in a project/disposable environment; use `with TraceProcessor(trace=..., config=TraceProcessorConfig(bin_path=...)) as tp:` and consume query rows before closing. `bin_path` should name the native binary. DataFrame conversion needs optional pandas/numpy; row iteration does not. See [Python API](https://perfetto.dev/docs/analysis/trace-processor-python).
- Repeated/fleet metrics -> use tested queries or [Trace Summarization](https://perfetto.dev/docs/analysis/trace-summary) with a versioned spec; pin tool/module/schema semantics. Do not label every duration aggregate a comparable performance metric.

DONE: reproduce the exact finding with SQL, inspect its timeline/interval context, and report observation separately from causal hypothesis and the next distinguishing experiment.
