# iOS and iPadOS Power Profiler

Primary sources: [Power Profiler](https://developer.apple.com/documentation/xcode/measuring-your-app-s-power-use-with-power-profiler), [WWDC25 session 226](https://developer.apple.com/videos/play/wwdc2025/226/), [Xcode 26 release notes](https://developer.apple.com/documentation/xcode-release-notes/xcode-26-release-notes), [Developer Mode](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device).

## 1. Establish eligibility and observer effects

- Use a physical iPhone running iOS 26+ or iPad running iPadOS 26+. Power Profiler was introduced in Xcode 26; use a compatible Xcode/Instruments installation on a Mac. Xcode 26's release baseline requires macOS Sequoia 15.6+; verify the requirements of the selected newer Xcode instead of reusing that minimum.
- Prepare the intended app/build, device pairing and existing profiling authorization. Enable Developer Mode only with the device owner's approval. Initiating or previous Mac pairing exposes the setting; Settings > Privacy & Security > Developer Mode requires restart and post-restart confirmation/passcode.
- Record app identity, installation route, selected device and process. Selecting All Processes records system power only, not the app's power-impact metrics.
- Charging through cable or MagSafe makes reported overall system power usage **0**. This is a measurement limitation, not proof of zero energy use. For connected system-power measurements, use wireless debugging and no charging connection.
- Xcode keeps Apple silicon awake while paired. Wireless connection removes charging bias, not the pairing observer effect. Use detached on-device recording to investigate sleep/wake or long-background behavior; keep pairing/connection conditions matched across A/B.

## 2. Capture a reproducible connected scenario

1. Select the physical device as Xcode's run destination. Choose Product > Profile; this builds/installs the configured Profile build, so record its optimization and diagnostic settings.
2. Choose Blank in Instruments' template window, add Power Profiler, and choose the target device and app/extension. Use Launch or Attach recording mode for process metrics, as required by the Xcode 26 release notes. Add an available CPU profiler or other diagnostic instrument only when needed; hold the instrument set constant for comparisons.
3. Start recording, perform the planned scenario, then stop. Preserve the trace and exact ROI; include completion/background work relevant to the question, not just a visually convenient spike.
4. Expand Power Profiler and the app track. Select the same scenario interval in each recording and inspect its summary alongside charging state, thermal state, display brightness and sleep/wake coverage.
5. Validate that the intended process and subsystem lanes contain data. A system-only trace, charging-zero system lane or absent samples is not an app-power baseline.

## 3. Capture detached field or background behavior

1. With approved Developer Mode enabled, open Settings > Developer > Performance Trace. Enable Performance Trace, follow device prompts, set Tracing Mode to Power Profiler, and enable the target in Monitored Apps.
2. WWDC25 specifies monitored apps installed by Xcode, TestFlight or enterprise distribution. Verify the target actually appears; do not promise arbitrary App Store app monitoring. TestFlight installation itself does not generally need Developer Mode, but this tracing procedure does.
3. Open Control Center; tap Add (+), Add a Control, then add Performance Trace. Use this current Apple procedure instead of the older Settings > Control Center route in the secondary article.
4. Disconnect from Xcode/charging as required by the experiment. Tap Performance Trace to start, reproduce the real scenario, then tap it again to stop. Apple documents collection for up to 10 hours; choose a bounded session appropriate to the question.
5. In Settings > Developer > Performance Trace, use the trace's Share button. Obtain authorization for the destination and sensitive contents before AirDrop/sharing.
6. On the Mac, expand the received `.aar` file in Finder into `.atrc`, then open it in Instruments. These are Apple trace artifacts, not Perfetto protobuf files. On-device Time Profiler uses a lower sample rate to reduce observer effect; compare like collection modes and avoid treating missing short calls as proof they did not run.

Recording can happen without a connected Mac; initial setup and later Instruments analysis are separate dependencies. The phrase "without Xcode" in the Medium article does not remove them.

## 4. Interpret, correlate, and verify

- Overall system power is a fraction of total battery energy consumed per hour, displayed for example as `%/hr`; it is not directly app-only watts, nor a predicted percentage-point drop in arbitrary future usage.
- CPU/GPU/display/network power-impact lanes are relative scores. Higher is greater impact. Apple permits comparing these lanes to prioritize investigation and comparing recordings on the same device; metrics differ across device models. Prefer the same physical device and exact metric for before/after work. Do not convert scores to watts or sum them into a claimed total battery cost.
- CPU impact -> correlate the interval with the CPU profiler's Call Tree and Heaviest Stack Trace. The WWDC example diagnoses eager off-screen thumbnail creation and repeated invariant file decoding; lazy creation/caching are justified only when the workload evidence matches.
- GPU impact -> investigate rendering with supported Metal tools; display impact -> inspect brightness/content and appearance; networking impact -> correlate Network Connections/HTTP Traffic with request frequency and transferred data. Preserve user-visible behavior and recheck other subsystems after a change.
- Xcode Energy Gauges, XCTest performance metrics, Organizer, MetricKit and App Store Connect can supply complementary development/field context. They are not interchangeable measurements of this ROI's energy; do not invent a general-purpose XCTest power metric or infer watts from CPU metrics.
- Recapture multiple matched trials after one justified change. Check the original scenario, functional/latency guardrails, all relevant impact lanes and system conditions. Report score changes as score changes, not universal battery-life improvements.

DONE: the real trace has required system/app lanes in the intended interval; build/device/connection state and units are known; the before/after conclusion stays within the captured evidence. Missing platform or device access -> provide the exact capture prerequisite and mark the workflow unexercised.
