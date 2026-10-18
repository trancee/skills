# Install Lean and control the Lake workspace

Baseline: Lean **4.35.0**, stable release 2026-10-12, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`. The `/latest/` reference currently describes **4.36.0-rc1**, not this stable release; use the consumer's exact version. FPIL and TPIL examples currently target 4.33.0 and require checking under the selected toolchain.

## Install by host and trust boundary

1. Prefer the [official VS Code + Lean 4 extension setup](https://lean-lang.org/install/). Open the extension's setup guide and the **project folder**, not just an unrelated loose file. Install `leanprover.lean4`, not a Lean 3 extension. Verify the editor and terminal select the same project/toolchain; do not accept workspace trust for an unreviewed project merely to dismiss a prompt.
2. For headless Linux/macOS, follow [manual installation](https://lean-lang.org/install/manual/): provide Git and curl, fetch `https://elan.lean-lang.org/elan-init.sh`, review it, then run the saved installer. `sh elan-init.sh --help` describes flags. For an isolated installation, set `ELAN_HOME` to a disposable directory **before** installing and on every later command; use `-y --no-modify-path --default-toolchain none` to avoid changing shell startup files or a default toolchain. Add that installation's `bin` to the current process's PATH. Normal user installation uses the installer's environment setup.
3. On native Windows, follow the same manual's Windows branch: Git/curl, reviewed `elan-init.ps1`, and a fresh terminal after PATH changes. The documented `powershell -ExecutionPolicy Bypass -f elan-init.ps1` is scoped to that invocation, not a reason to weaken global policy. WSL is a separate Linux environment: install the toolchain there and open that filesystem through the editor's WSL support. Do not mix native and WSL binaries/build artifacts.
4. Match the release's [supported platforms](https://lean-lang.org/doc/reference/4.35.0/platforms/): Tier 1 includes glibc Linux x86-64/aarch64, Apple Silicon macOS, and x86-64 Windows; Intel macOS is Tier 2. Check minimum OS/libc and actual release assets before assuming support for musl, a new architecture, or a source build.
5. Run from the intended project directory:
   ```bash
   elan show
   lean --version
   lake --version
   elan which lean
   ```
   `elan` installs/selects toolchains; `lake` is bundled with each Lean toolchain. A different package named lake is not a substitute. Preserve the complete distribution, including standard libraries and native linker support.

Source: [versioned elan reference](https://lean-lang.org/doc/reference/4.35.0/Build-Tools-and-Distribution/Managing-Toolchains-with-Elan/).

## Select versions without accidental migration

- Existing project: read `lean-toolchain`, `lakefile.toml` **or** `lakefile.lean`, and `lake-manifest.json` before invoking update commands. Respect its exact pin even when newer stable exists.
- `elan show` reports the selection source; a directory override can take precedence over `lean-toolchain`, and a nearer parent wins. Explicit `+toolchain` arguments and environment overrides can also select a different compiler. Diagnose this before editing the project pin.
- New standalone project: install a deliberate release and generate with it:
  ```bash
  elan toolchain install leanprover/lean4:v4.35.0
  lake +leanprover/lean4:v4.35.0 new VerifiedDemo std
  ```
  Enter the generated directory, inspect its configuration and `lean-toolchain`, then run `lake --wfail build`. `std` creates a library and executable; `lib`, `exe`, and `math` select different templates. `lake init` initializes the **current** directory, so use it only in a deliberately chosen empty directory.
- Mathlib: use the compatible Mathlib toolchain, not arbitrary latest Lean. Read `references/proofs-mathlib-trust.md` for new/existing projects, cache and proof validation.
- A migration changes the compiler and dependency set together. Review selected upstream release notes, update dependency constraints intentionally, resolve via `lake update`, inspect changed manifest/toolchain, obtain matching caches, and compile all affected targets. `lake update` is not a generic repair command: it can move dependency revisions and run package hooks.

## Build the changed code, not an unrelated default target

Lake's [workspace/target reference](https://lean-lang.org/doc/reference/4.35.0/Build-Tools-and-Distribution/Lake/) is authoritative for the selected release.

| Operation | Command / interpretation |
| --- | --- |
| Normal project build | `lake --wfail build`; only configured default targets and dependencies |
| Specific module | `lake --wfail build +VerifiedDemo.Proofs`; discovers/builds imports |
| One file in package environment | `lake env lean -DwarningAsError=true VerifiedDemo/Proofs.lean`; imports must already be built |
| Interpret a program | `lake env lean --run Main.lean`; calls `main` |
| Build and run executable | `lake exe verifieddemo`; use the actual configured target name |
| Existing test/lint driver | `lake test`, `lake lint`; inspect configuration, driver coverage and exit status |
| Extra proof validation (4.35+) | `lake check`; read proof/trust reference before running on untrusted input |

`lake env` configures search paths; it does **not** build missing imports. Build their module targets first. A file outside the default import graph can remain unchecked after a successful default build. Keep new proof modules in the intended library graph and explicitly build each changed module. Use the existing module header/export style: Lean's newer `module`/`public import`/`public section` system changes visibility, so a namespace alone does not export a declaration across modules.

Commit source/configuration, `lean-toolchain`, and the manifest according to the repository convention. Keep `.lake` build outputs and downloaded dependencies out of the skill/consumer source commits. `.olean` files are compiler-version-specific; rebuild at the proper pin instead of copying incompatible artifacts or deleting a manifest to force resolution.

## Failure boundaries

- Executable missing: inspect PATH and `ELAN_HOME`, then `elan show`; install the actual pinned toolchain. Do not overwrite global defaults to fix one project.
- Download/TLS/proxy failure: preserve certificate verification; correct network/proxy trust or obtain verified matching release assets. Report unavailable checking, not proof success.
- Unknown module/package or missing `.olean`: confirm project root, exact case-sensitive module path, dependency pin and the import build. Adding `import Mathlib` cannot install Mathlib.
- Linker/native compilation failure: distinguish Lean elaboration from the native compiler/linker stage; use the release's supported host/build prerequisites.
- Stale editor result: save the file, wait for checking, inspect InfoView diagnostics, and compare against a terminal check from the same root/version. Restart the file/server only after fixing the environment; no blanket cache deletion.

Gate: the actual selected release builds every changed module and executes the relevant program/tests; dependency changes and unavailable host paths are explicit.
