# Tools, versioning, source builds

Sources: [Trace Processor](https://perfetto.dev/docs/analysis/trace-processor), [CLI reference](https://perfetto.dev/docs/reference/trace-processor-cli), [releases](https://github.com/google/perfetto/releases), [build instructions](https://perfetto.dev/docs/contributing/build-instructions).

## 1. Use the smallest matching tool

1. UI only -> open [ui.perfetto.dev](https://ui.perfetto.dev); local files are processed in-browser by default. Share links/upload and external symbol services are separate disclosure decisions.
2. CLI -> acquire the official wrapper, inspect it, then invoke its help/version. `trace_processor` is a Python wrapper that fetches/caches the platform native binary on first use; it is not itself a self-contained native executable:

```bash
curl -fLO https://get.perfetto.dev/trace_processor
python3 trace_processor --version
python3 trace_processor --help
```

Download from the trusted origin, review before execution, and record the resolved version. For reproducible/offline use, download the matching platform archive from a selected release, check the release-provided SHA-256, extract it, and invoke `trace_processor_shell` directly. The v59.1 Linux amd64 release zip SHA-256 is `7deb8c2572c6ae7ec80cd719d388041079827b0c44a1659694d5d88faa4f501e`; verify another release/platform against its own metadata. Keep archive, SDK and wrapper versions distinct.

3. Linux capture -> use the matching `tracebox` release or official wrapper. It bundles tracing service/probe/client applets. Android ordinarily uses its shipped `perfetto` and system daemons; inspect that target's supported sources/flags rather than assuming it matches the host release.
4. Upstream offers a separate [official AI skill](https://perfetto.dev/docs/getting-started/using-ai). Do not silently install it or create two discovered packages named `perfetto`; choose the intended package/scope explicitly. This repository package is independently authored and does not bundle upstream's binary installer or claim all its specialized workflows.

## 2. Build only when binaries/SDK do not suffice

For Perfetto tools themselves, GN/Ninja is the standalone build; the two-file C++ SDK can use a consumer's CMake without a full checkout.

```bash
git clone --branch v59.1 --depth 1 https://github.com/google/perfetto.git perfetto-src
# Run the following from the checked-out source root.
tools/install-build-deps
tools/gn gen out/release --args='is_debug=false'
tools/ninja -C out/release trace_processor_shell tracebox
```

`install-build-deps` downloads toolchains/dependencies; review network/disk requirements first. Add `--android`, `--ui`, `--linux-arm`, or `--rust` only for those targets. For Android, set `target_os="android"` and the target CPU in a separate GN output directory. UI work -> follow [UI development](https://perfetto.dev/docs/contributing/ui-getting-started), not the SDK CMake example. AOSP builds use their own environment and `m traced traced_probes perfetto`; standalone omits some internal Android dependencies.

For source changes, run the target's existing native/diff tests and smoke the resulting executable on a real trace; follow [contributor testing](https://perfetto.dev/docs/contributing/testing). GN `BUILD.gn` is authoritative; generated Android.bp/Bazel outputs use upstream generators rather than hand edits. Verify current toolchain requirements from the selected checkout; old platform-version examples are not current compatibility guarantees.

## 3. Preserve symbols and trace format semantics

- Native profiles -> keep unstripped binaries/debug info with the same Build IDs as the captured mappings. Use optimized builds with debug info when measuring shipping-like behavior. Obtain matching Java deobfuscation maps where applicable.
- [Symbolization](https://perfetto.dev/docs/learning-more/symbolization) -> use `trace_processor bundle INPUT OUTPUT` and explicit `--symbol-paths`/matching `llvm-symbolizer` for offline symbols. Confirm newly resolved names. Remote debuginfod retrieval is opt-in and may disclose requested Build IDs; do not enable it implicitly.
- [Merging](https://perfetto.dev/docs/analysis/merging-traces) -> use supported archive/manifest merge tools, validate machine and clock alignment. Concatenation is not a trace merge.
- Exported SQLite is not a Perfetto protobuf trace and does not carry the full live PerfettoSQL environment. The `perfetto` export archive is version-coupled; preserve the processor version. `convert` changes trace formats; `export` writes parsed tables.
