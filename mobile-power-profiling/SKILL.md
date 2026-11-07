---
name: mobile-power-profiling
description: "Measures and investigates iOS/iPadOS and Android app power consumption. Use when profiling battery drain, Instruments Power Profiler or on-device Performance Trace, Android Studio ODPM power rails, or controlled before/after energy comparisons. Don't use for battery health or charging advice, desktop/server energy measurement, distributed tracing, or unsupported per-app wattage claims."
compatibility: "Apple capture requires a physical iOS/iPadOS 26+ device and compatible Xcode/Instruments on a Mac; detached recording requires approved Developer Mode. Android ODPM requires supported physical hardware (documented Pixel 6+) and Studio Hedgehog+. Comparison CLI: Python 3.10+, stdlib only."
metadata:
  category: "testing-quality"
  source: "https://developer.apple.com/documentation/xcode/measuring-your-app-s-power-use-with-power-profiler; https://developer.android.com/studio/profile/power-profiler"
  sourceVersion: "Apple Xcode 26 and WWDC25 session 226; Android Studio live docs and A/B article 2024-04-17; five requested sources accessed 2026-11-07"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-11-07T19:45:15+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-11-07T19:45:15+01:00"
---

# Mobile power profiling

PATHS: resolve resources from this activated package, not the app repository. This skill supplies capture/analysis procedures and a descriptive comparison CLI, not installed profilers, device access or fabricated power data.

## Step 1: Define the question and measurement boundary

1. RECORD the symptom or implementation comparison, app/build, physical device/model/OS, tool version, workload, foreground/background state and evidence already available. Separate the capture device from the analysis host.
2. iOS/iPadOS -> READ [references/ios.md](references/ios.md). Android -> READ [references/android.md](references/android.md). For a cross-platform comparison, run separate experiments; platform scores and sensors are not one common energy scale.
3. RECORD metric, unit and attribution: Apple overall system battery-energy fraction/hour versus relative app subsystem impact; Android ODPM whole-device rail power versus battery-gauge observations. Select app/process explicitly where the tool supports app impact.
4. READ [references/sources.md](references/sources.md) when reconciling the five source articles, old UI instructions, version eligibility or broad battery-saving claims. Primary platform documentation governs; numeric demonstrations are not universal thresholds.
5. Obtain authorization before Developer Mode/debugging changes, elevated/device capture, app restarts or sharing traces. Preserve source recordings and sensitive identifiers; perform local analysis without unapproved uploads.

DONE: the supported capture route, required signal, units, device/app identity and attribution limits are explicit. No eligible tool/device -> name that prerequisite and complete reachable analysis, not simulated measurement.

## Step 2: Plan and capture comparable evidence

1. COPY [assets/experiment.md](assets/experiment.md) and READ [references/comparison.md](references/comparison.md) before a baseline/candidate experiment. Define A/B, one implementation difference, repetitions/order, exclusion criteria and functional/latency guardrails.
2. Define a complete workload ROI and relevant deferred/radio-tail cost. Match device, builds/instrumentation mode, app/data/cache state, brightness, network, charging/pairing and thermal/background conditions. Treat differing completion durations as a power-versus-energy question, not an excuse to omit unfinished work.
3. Follow the platform reference for actual recording. On Apple, charging makes reported system power zero and Xcode pairing changes sleep behavior; use detached collection for those real-world conditions. On Android, inspect supported rails and profileable low-overhead collection rather than assuming the selected app owns all rail activity.
4. Preserve raw traces, start/stop markers and ROI timestamps/clock. Check target lanes/sources, coverage, charging state, loss/missing samples and measurement granularity before reducing readings. File existence or a zero lane is not capture success.

DONE: each usable recording contains the required signal and completed scenario under documented conditions; rejected or unavailable recordings have an explicit reason.

## Step 3: Diagnose and compare

1. Correlate the high-power interval with CPU stacks/scheduling, render/display work, requests/radio behavior or background tasks. Prioritize the evidenced subsystem; power correlation alone does not identify a function, lock owner or causal defect.
2. Apply one justified change, then recapture the original scenario. Check other subsystem costs, duration/energy and behavior guardrails; lazy loading, caching, batching or media changes are candidates only when workload evidence and product requirements support them.
3. For homogeneous, already-reduced ROI readings, COPY [assets/readings.csv](assets/readings.csv), populate real A/B pairs with trace provenance, then RUN `python3 <skill-directory>/scripts/compare-runs.py readings.csv`. Read the CSV contract in `references/comparison.md` first. The CLI does not parse native traces or recover missing measurements.
4. Inspect pairwise deltas/spread and the ratio-of-means relative change. Negative delta means lower B; a zero baseline produces an undefined relative change (`null`). Mixed/noisy outcomes need additional matched captures, not a claimed significant win.
5. Android trace SQL beyond the Studio summaries -> use the separately available `perfetto` skill after verifying captured power sources/schema. Apple `.aar`/`.atrc` artifacts remain Instruments inputs, not Perfetto traces.

DONE: a reproducible result is tied to the same metric/device/ROI, individual captures, uncertainty and relevant code/workload evidence; improvement claims stay within that boundary.

## Step 4: Report and verify the final path

1. COPY [assets/findings.md](assets/findings.md) or use its fields in a concise response. Separate observation, interpretation and next experiment. Name actual rails/lane, units, build/device, repetitions, exclusions and provenance.
2. Instrumentation/optimization changes -> exercise the changed app path and repeat measurement on the intended device. Comparison-tool changes -> run the real CLI with known paired values, a zero baseline and mismatched/invalid input; verify computed deltas and meaningful failure exits.
3. Close owned profiler/recording/query sessions and remove disposable smoke outputs. Preserve user traces and requested results. State unavailable platform, device, UI and production-monitoring paths explicitly.

## Error Handling

- Apple system lane reads zero while charging -> remove charging under the approved experiment or report the limitation; do not call it a power-free workload.
- Apple app-impact lanes missing -> check app/process selection, monitored-app eligibility, device OS and collection mode; All Processes is system-only.
- Android rails absent -> inspect physical hardware/source support; gauge data can supply a different device-level observation, not invented app power.
- Background issue disappears while paired -> use detached recording and preserve the field scenario and connection state.
- Comparison exits 2 -> fix the reported header, pair/context, numeric or unit contract; separate heterogeneous datasets instead of coercing them.
- Apparent improvement lacks corroboration -> inspect other subsystems, ROI completion, noise and trace coverage; report a bounded observation and distinguishing experiment.
