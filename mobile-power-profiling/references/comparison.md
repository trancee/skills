# Controlled before/after power comparisons

Sources: [Apple power workflow](https://developer.apple.com/documentation/xcode/measuring-your-app-s-power-use-with-power-profiler), [WWDC25 comparisons](https://developer.apple.com/videos/play/wwdc2025/226/?time=979), [Google A/B workflow](https://android-developers.googleblog.com/2024/04/how-to-effectively-ab-test-power-consumption-for-your-android-app-features.html). The pairing/CSV reduction below is this skill's conservative protocol, not a platform-provided significance test.

## 1. Predeclare the experiment

1. Copy `assets/experiment.md` from the activated package. Define one implementation difference, exact device/builds and scenario, workload scale, marker/ROI boundaries, measurement method, required signals and user-visible guardrails.
2. Hold the physical device, OS, app build mode, instrument set, dataset, cache/app state, account/settings, display/brightness, power/charging connections, network conditions and thermal/background state constant. Record unavoidable differences rather than erasing them from the conclusion.
3. Collect repeated A/B pairs with alternating or randomized order to reduce drift. Pair comparable conditions, not arbitrary sorted runs. Choose repetitions and exclusions in advance; aim for at least three pairs for a first descriptive comparison and collect more when noise dominates. No fixed count guarantees statistical confidence.
4. For scenario-dependent effects, repeat at realistic small/large data sizes and network states as separate experiments. Do not average unrelated conditions or different device models into one score.

## 2. Reduce the same metric and interval

- Select equivalent complete-work ROIs and include relevant deferred/radio-tail cost. Use identical fixed durations for this script's homogeneous comparison; if completion time differs, compare equivalent completed-work energy in a separate duration-aware analysis and report runtime alongside power. Do not clip the slower implementation to hide unfinished work.
- Distinguish rate from amount: `energy_J = average_power_mW * duration_s / 1000`; `energy_mWh = average_power_mW * duration_s / 3600`. These equations assume the reported power is the valid time-weighted mean over the interval. A lower peak alone is not lower total energy.
- For irregular power samples, integrate over valid time intervals; for cumulative energy counters, use valid boundary deltas and sampling/time contracts. Detect resets, missing intervals and incomplete bounds before reduction. Do not bridge gaps or substitute a plain sample mean without a justified sampling model.
- Keep Android rail sets fixed; document summed rails and whether they are independent. Keep Apple's exact impact lane/device fixed. Relative impact scores are not physical energy and cannot be added to measured watts or converted with these equations.
- Record the original trace, ROI timestamps/clock and profiler summary/query that supplied every reading. Battery percentage/hour is a system-rate observation, not interchangeable with battery health, remaining charge or impact score.

## 3. Run the descriptive comparison tool

Copy `assets/readings.csv`, which intentionally contains only the header. Populate real reduced readings; do not ship the template as measurement evidence. The exact columns are:

| Column | Contract |
|---|---|
| `pair` | Nonempty run-pair identifier, with one A and one B |
| `variant` | `A` baseline or `B` candidate |
| `device` | Same physical-device identifier for every row; avoid publishing sensitive serials |
| `scenario` | Same scenario/ROI definition; bind to the experiment ledger |
| `metric` | Same exact lane or selected-rail aggregate; e.g. CPU power impact or named nonoverlapping rail set |
| `unit` | `mW`, `J`, `mWh`, `battery_percent_per_hour`, or `power_impact` |
| `duration_s` | Same positive ROI duration across this comparison |
| `value` | Finite, nonnegative reduced reading in that unit |

Run from any target workspace using the resolved package path:

```bash
python3 <skill-directory>/scripts/compare-runs.py readings.csv
# Or pipe the same CSV to .../compare-runs.py -
```

The CLI requires Python 3.10+ and no third-party packages. It writes JSON to stdout, actionable errors to stderr, and exits 2 for invalid input. It rejects mixed contexts, unsupported units, duplicate readings, unmatched pairs and fewer than two complete pairs. Keep output alongside the experiment; it is not an Instruments/Studio raw-trace importer.

Output includes context, each pair's A/B/delta, A and B means, paired-delta mean/median/range, and `change_percent_of_baseline_mean = 100 * (Bmean / Amean - 1)`. Negative means lower B. For a zero baseline mean, relative change is `null`, not zero or infinity. It uses the ratio of means, not an average of per-run percentages.

## 4. Judge the result within its boundary

1. Examine paired deltas and spread, not just aggregate direction. Mixed-sign or noisy changes warrant more matched measurements or a distinguishing experiment. The script supplies no confidence interval, p-value, pass/fail budget or causal proof.
2. Check CPU/GPU/display/network effects, measured workload duration/energy and functional/latency guardrails. A CPU-score decrease can trade for networking or rendering costs; a lower rate can run longer and consume more energy.
3. For causality, correlate the same ROI with code/workload evidence and change one justified cause. Keep exclusions visible and do not choose only favorable trials.
4. Copy `assets/findings.md` for reporting. State exactly what was measured, on which device and under which conditions, and what remains unknown. A device-rail or impact-score improvement does not automatically predict percentage battery-life gains in production.

DONE: repeated matched data, trace provenance, correct units and ROI coverage support a bounded result, with measurement noise and other subsystem/behavior tradeoffs reported.
