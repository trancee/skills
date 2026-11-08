# Standalone setup, bounded fuzzing and replay

Sources: [v0.30.0 README](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/README.md), [release](https://github.com/CodeIntelligenceTesting/jazzer/releases/tag/v0.30.0), [advanced options](https://github.com/CodeIntelligenceTesting/jazzer/blob/v0.30.0/docs/advanced.md), [libFuzzer](https://llvm.org/docs/LibFuzzer.html). Inspect the selected binary's `--help`; live docs may describe options differently from the pinned binary.

## 1. Install the matching release and JDK

1. Download the selected archive from GitHub releases and verify the asset's published digest before extraction. v0.30.0 Linux x86-64 archive: `jazzer-linux-x86-64.tar.gz`, SHA-256 `6eeaf0026d75599b07527d93b576593ce847cfca8b337a579971a5a9cdf792d0`. Other architectures/releases have their own digests.
2. Preserve `jazzer` (or `jazzer.exe`) alongside `jazzer_standalone.jar`; the native launcher starts its own JVM. Set `JAVA_HOME` to the intended full JDK and verify both compiler/runtime versions. This package smoke used JDK 21 and Java 17 target bytecode, not an assurance that the newest installed JDK is compatible.
3. Run `jazzer --version` and `jazzer --help`. Upstream lists Linux x86_64/arm64, macOS12+ x86_64/arm64 and Windows x86_64. JNI sanitizer support has additional compiler/runtime/platform requirements.
4. Missing libjvm -> inspect JAVA_HOME/JDK library location and native architecture first. A recent bytecode version rejected by instrumentation -> select a supported target JDK/compiler pairing; do not turn off instrumentation to make a smoke run pass.

## 2. Compile and run a narrow target

Copy `assets/Base64Target.java` to a disposable workspace. Set `JAZZER_DIR` to the extracted release directory. From that workspace on POSIX:

```bash
mkdir -p classes corpus artifacts reproducers
javac --release 17 -cp "$JAZZER_DIR/jazzer_standalone.jar" \
  -d classes Base64Target.java
"$JAZZER_DIR/jazzer" --cp=classes --target_class=example.Base64Target \
  '--instrumentation_includes=example.**' \
  --reproducer_path=reproducers \
  -runs=10000 -max_total_time=30 -max_len=4096 \
  -artifact_prefix=artifacts/ corpus
```

This valid corpus can be empty initially; add small accepted/rejected parser seeds for better depth. Fuzzing writes new coverage inputs to the first corpus directory. Inspect logs for target instrumentation, executions, coverage/features and termination reason. Example-package instrumentation covers the probe; for a real application include the implementation packages too. Standard libraries/JVM internals are excluded by default.

- Standalone entry point is `public static void fuzzerTestOneInput(...)`, with a supported raw/provider/typed signature. A `fuzzerInitialize` can prepare invariant setup and `fuzzerTearDown` can clean task-owned resources; per-input state must still reset.
- `--cp` is an explicit classpath. Quote it and use `:` on POSIX, `;` on Windows. The README's `java -cp` semicolon example is not a POSIX shell command; prefer the supplied launcher or the exact full Maven runtime dependency classpath.
- Jazzer options use double dash/underscores (`--target_class`, `--instrumentation_includes`); libFuzzer options use single dash (`-runs`, `-max_len`, `-seed`, `-dict`, `-use_value_profile`). Corpus/artifact paths are positional or libFuzzer paths, not JVM options.
- `--jvm_args` overrides JAVA_OPTS; list separators are platform classpath separators and the entire value needs shell quoting. Retain stack traces with `-XX:-OmitStackTraceInFastThrow`; JDK21 dynamic-agent policy may warn. Older JVM-specific flags such as CriticalJNINatives do not apply to all JDKs.

## 3. Preserve and replay a finding

1. Save the command, pin, classpath, target/signature, instrument scope, stack, `DEDUP_TOKEN`, raw artifact and any generated Java reproducer. A typed corpus is serialized arguments; provider bytes are a consumption stream. Do not edit them as if they were input text.
2. Stop or work on a snapshot before running `scripts/inventory-corpus.py` to record bytes and SHA-256. The script does not judge coverage or minimize inputs.
3. Replay with identical target/configuration, using the artifact file as the only positional input:

```bash
"$JAZZER_DIR/jazzer" --cp=classes --target_class=example.Base64Target \
  '--instrumentation_includes=example.**' artifacts/crash-HASH
```

The named class must be the class that originally failed; `Base64Target` above illustrates argument placement, not an assumed crash in that example.

4. If emitted, inspect/compile the actual Java reproducer filename with the target and dependencies, then run it outside Jazzer. v0.30.0 emits `Crash_<sha1>.java` (some documentation says `Crash-<sha1>.java`); use the logged path, not a guessed glob. Provider reproducers may need Jazzer API classes; hooks/sanitizer-only findings may need instrumented replay and may not fail in plain Java. Record which route reproduced the same finding.
5. Minimize into a new artifact path, preserving the original:

```bash
"$JAZZER_DIR/jazzer" --cp=classes --target_class=example.Target \
  -minimize_crash=1 -exact_artifact_path=artifacts/minimized \
  -max_total_time=30 artifacts/crash-HASH
```

Recheck the same defect/stack, not just any exception after minimization. Fix the root cause, replay original and minimized inputs, then fuzz fresh again. Nonzero status for an expected finding is evidence, not a reason to suppress the error.

## 4. Maintain corpus and budgets

- Separate generated coverage corpus from reviewed regression findings. Snapshot before merge/minimization; `-merge=1 new-corpus old-corpus` retains coverage-relevant entries in a new directory but does not replace crash triage.
- `-runs=0 corpus` exercises saved corpus inputs without a new mutation campaign; a single file positional input is the explicit replay route. Use existing regression tests to lock down real fixed behavior.
- Bound overall time, executions, input length and per-input resource use. No findings in a budget means only no observed finding, not complete coverage/security. A timeout/OOM may indicate a harness limit or a real algorithmic issue; reproduce/classify before changing limits.
- `-fork=N` or `-jobs=N`/`-workers=N` can distribute standalone work after the target is reproducible. Give each campaign owned artifacts and limits, preserve logs, and never start concurrent fuzz methods in one JVM as a substitute.

DONE: the instrumented target executes/mutates, finds or replays a known defect when checking the finding path, and preserves artifacts and truthful termination/coverage evidence.
