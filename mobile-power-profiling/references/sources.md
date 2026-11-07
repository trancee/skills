# Source authority and reconciliation

All five requested pages were read on 2026-11-07. Treat examples as experiments, not general thresholds. Refresh primary documentation when device/tool eligibility or UI differs.

| Source | Use | Boundary or correction |
|---|---|---|
| [Apple: Measuring your app's power use with Power Profiler](https://developer.apple.com/documentation/xcode/measuring-your-app-s-power-use-with-power-profiler) | Connected and on-device capture, metrics, charging/sleep limitations, transfer workflow | Primary. iOS/iPadOS 26+, charging forces reported system power to zero; app impact values differ across device models. |
| [Android: Power Profiler](https://developer.android.com/studio/profile/power-profiler) | ODPM support, rail availability, gauge fallback | Primary. Physical Pixel 6+ route; rail measurements are device-wide and available rail sets vary. API 29+ wording does not imply ODPM on every Android 10 device. |
| [DEV: WWDC 2025 iOS Power Optimization](https://dev.to/arshtechpro/wwdc-2025-ios-power-optimization-advanced-profiling-techniques-that-actually-work-4a10) | Secondary explanation of Apple examples and subsystem triage | CPU impact 1 versus 21 and system 10.5%/hr are example observations, not universal budgets or a defined critical threshold. Automated tests and field metrics are complementary, not a claimed general XCTest wattmeter. |
| [Medium: Measure Your iOS App's Battery Usage Without Xcode](https://shubhanshubb.medium.com/measure-your-ios-apps-battery-usage-without-xcode-7a6a831676c1) | Secondary walk-through of detached on-device recording | Recording can be detached; provisioning/Developer Mode and Instruments analysis are separate requirements. Use Apple's current Control Center Add a Control path, rather than the post's Settings > Control Center path. |
| [Android Developers: A/B power testing, 2024-04-17](https://android-developers.googleblog.com/2024/04/how-to-effectively-ab-test-power-consumption-for-your-android-app-features.html) | Workload isolation, trace markers, repetitions, video-resolution experiment | Primary experiment; screenshots reflect 2024 Studio. 1,352 versus 741 mW is about 45% lower power in the selected measured rails/window, not proof of 45% better battery life or app-only power. |

## Supplemental primary evidence

- [Apple WWDC25 session 226](https://developer.apple.com/videos/play/wwdc2025/226/): confirms monitored apps installed by Xcode, TestFlight or enterprise distribution, lower-rate on-device Time Profiler sampling, and the demonstrated code-level diagnoses. The LazyVStack and cached decoding fixes apply to those workloads, not every app.
- [Android profiling overview](https://developer.android.com/studio/profile) and [system trace view](https://developer.android.com/studio/profile/cpu-profiler): use current task/recording controls and actual app eligibility; power-specific ODPM documentation controls attribution even where generic profiler labels say "app battery usage".

## Evidence hierarchy

1. Actual tool/device capability and captured signal coverage.
2. Current Apple/Google documentation and first-party sessions.
3. First-party experiment details, scoped to the measured configuration.
4. Secondary explanations; omit unsupported claims rather than expanding them into recipes.

No source supplies a universal cross-platform power budget, direct conversion of Apple's impact score to watts, or universal per-app attribution for Android rails. Establish those boundaries in the report.
