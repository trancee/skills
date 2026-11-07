# Android Studio Power Profiler

Primary sources: [Power Profiler](https://developer.android.com/studio/profile/power-profiler), [profiling overview](https://developer.android.com/studio/profile), [system trace view](https://developer.android.com/studio/profile/cpu-profiler), [2024 A/B experiment](https://android-developers.googleblog.com/2024/04/how-to-effectively-ab-test-power-consumption-for-your-android-app-features.html), [Trace API](https://developer.android.com/reference/android/os/Trace).

## 1. Check target and build eligibility

- Android Studio Hedgehog introduced Power Profiler. Use an available current Studio profiler with a physical supported device. Google's documented ODPM route is Pixel 6 and later Pixel devices; the power docs also state Android 10/API 29+. That API minimum is not a promise of rails on every Android 10 device, emulator or vendor device.
- Inspect the actual recording's available rails. CPU Big/Mid/Little, GPU, memory, display, WLAN, cellular, camera, GPS, sensors and storage can differ by device; do not assume the full documented list is present.
- Prefer a release-like profileable build and low-overhead profiling. Current general profiler requirements recommend AGP 7.3+ and an API29+ test device with Google Play; ODPM imposes the additional physical-device eligibility above. Verify the final merged manifest/build configuration rather than assuming profileability from a source manifest.
- A `<profileable android:shell="true" />` element inside `<application>` enables shell profiling where supported. Confirm project/device policy before changing profiling eligibility; do not enable debug/security settings on a user's device without authorization.
- Complete-data/debuggable profiling has overhead and supports extra signals such as interactions/allocations. Keep the same build/collection mode on A/B; use debuggable evidence as a diagnostic follow-up, not a shipping-energy comparison against a profileable candidate.

## 2. Capture System Trace using current Studio controls

1. Select the run configuration, supported physical device and release build variant (Build > Select Build Variant). Choose More actions > Profile 'app' with low overhead; the name follows the actual run configuration.
2. In the Profiler Home tab, select the intended app process. Choose the task that records a System Trace/system-wide activity; inspect available tasks instead of assuming screenshots from 2024 match current Studio.
3. Use Start profiler task from to choose startup or attachment to the running process. Include startup only when startup belongs to the experiment; isolate playback or another operation after a defined action when that is the question.
4. Start the task, perform the scripted workload, stop the recording, and wait for parsing. Preserve the raw recording and chosen ROI; inspect Power Rails, Battery, CPU/thread activity and other required signals.
5. Record the summary for the same interval and fixed rail set in both variants. Past Recordings retains tasks for the current Studio session. Use Export recording where the trace type supports it for durable evidence; Import recording or drag a supported trace into Studio for later comparison. Do not treat a screenshot alone as sufficient reproducibility evidence.

The 2024 blog uses Run Configuration > Profiling > Start this recording on startup > CPU Activity > System Trace. That is useful historical context, not the required menu sequence for newer task-based Studio.

## 3. Mark the workload and its deferred cost

- Use existing markers or `android.os.Trace` begin/end sections to locate the operation. End synchronous sections on the same thread, normally in `finally`; cross-thread work needs the supported asynchronous API and matching name/cookie, not unmatched synchronous ends. Ensure app trace markers are actually present in the recording.
- Define the ROI in the experiment before measuring. Include required background completion, decode/render work and radio tail energy after a request, or report operation-only and tail windows separately with identical definitions. Do not truncate immediately at response arrival and claim full networking cost.
- Match network type/signal, brightness/display state, battery/charging state, thermals, app/data/cache state, other active processes and profiling overhead. Alternate AB/BA runs with matched cooldown conditions; reject interrupted/uncovered recordings under predeclared rules.

## 4. Interpret rails and battery gauges correctly

- ODPM measures the **whole device**, not the selected app. Correlate rail activity with app CPU scheduling, render work, requests and background tasks; corroborate before blaming one app/function. Other apps and the OS create noise.
- Record exactly which rails and units are used. A selected-rail sum is not automatically complete device power; avoid double-counting overlapping aggregate/subsystem readings. Compare the same rail set on the same device.
- Power in `mW` is a rate; energy in `J`/`mWh` is an integral. Use the profiler's documented ROI reduction or a validated time-weighted calculation. A raw sample average is not equivalent when sample spacing differs.
- Devices without ODPM may expose capacity `%`, remaining charge `µAh`, or instantaneous current `µA` through gauges/coulomb counters. These remain battery/device observations. Charge is not energy, instantaneous current is not average power, and current-to-watts requires valid voltage, sign, timing and battery/charging assumptions. Do not invent absent rail data or claim app-only watts from these gauges.
- The blog's 30-second video comparison reports about 1,352 versus 741 mW in selected WLAN/CPU/memory rails, approximately 45% lower measured selected-rail power. It does not establish a universal 45% app battery saving or a preferred video quality for all workloads.

## 5. Diagnose and close the loop

- CPU rail increase -> inspect scheduled app work and repeated background tasks; GPU/display -> inspect frame/render/content behavior; WLAN/cellular -> inspect transfer frequency/size, signal and radio tail. Wakelocks can matter, but power alone neither identifies their holder nor proves a lock is unnecessary.
- Choose one evidence-backed change: for example batching/caching requests, delaying optional media until requested, reducing unnecessary decode/render work or releasing an observed unused wakelock. Preserve functionality, freshness, task completion, quality and latency requirements.
- Repeat the same scenario on the same device/build mode/rail set. Report trial spread, missing signals and system noise; use the full relevant workload interval and inspect regressions in other rails before concluding.
- Need exported Android trace SQL or detailed scheduler attribution -> invoke the separate `perfetto` skill if available; its basic scheduling config is not an ODPM capture recipe. Inspect captured power-source/schema availability first, rather than inventing power tables or app energy allocations.

DONE: the physical-device recording contains the required rails/gauges and ROI; attribution stays device-wide unless separately evidenced; repeated matched measurements and workload/code context support the stated change. No eligible device -> report that prerequisite, not a fabricated measurement.
