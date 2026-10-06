# Installation and runtime

## Refresh gate

Before changing a host, read:

- Official install page: https://tamarin-prover.com/install.html
- Latest release and assets: https://github.com/tamarin-prover/tamarin-prover/releases/latest
- Release notes for the selected version

Record the selected version, asset/package origin, OS, architecture, and dependency compatibility. The baseline inspected for this skill is Tamarin Prover 1.12.0 (`82780bbaf3328a45f624ddb41e51bf75425f851c`, released 2026-03-07). Its release notes allow Maude through 3.5.1. Re-check the selected release rather than inheriting this range.

## Select one installation route

### Homebrew on macOS or Linux

```bash
brew install tamarin-prover/tap/tamarin-prover
```

Use the tap's packaged Maude and Graphviz dependencies. Pin or record the resolved formula version where reproducibility matters.

### Arch Linux

```bash
sudo pacman -S tamarin-prover
```

Confirm the distribution package version matches the analysis baseline.

### Nix

For a user profile:

```bash
nix-env -i tamarin-prover
```

For NixOS, add `tamarin-prover` to `environment.systemPackages` and rebuild the configuration. Prefer a pinned flake or nixpkgs revision for reproducible verification.

### Windows

Use WSL2 with Ubuntu. Install and run Tamarin inside WSL, not as a native Windows binary. Access Windows files under `/mnt/c/...`. For interactive mode, start Tamarin in WSL and open `http://127.0.0.1:3001` in the Windows browser.

### Release archive

1. Select an official release asset matching the host architecture and supported distribution.
2. Verify the downloaded digest against the digest published by GitHub Releases.
3. Extract the archive into a versioned location; place only the intended executable on `PATH`.
4. Install compatible Maude and Graphviz separately when the archive does not provide them.
5. Record the asset URL and SHA-256 digest.

Do not run an asset for a different architecture or silently replace a missing dependency with an arbitrary version.

### Source build

Use this route only for Tamarin development or a required unreleased feature.

1. Install Haskell Stack, Graphviz, and a release-compatible Maude.
2. Clone the official repository and check out an immutable tag or commit:
   ```bash
   git clone https://github.com/tamarin-prover/tamarin-prover.git
   cd tamarin-prover
   git checkout <tag-or-commit>
   make default
   ```
3. Add `~/.local/bin` to `PATH` if required.
4. Record the commit, compiler/Stack resolver, build command, and resulting binary digest.

The official guide notes that source builds install many Haskell dependencies and are substantially slower than packaged installs. If Stack fails after an update, refresh Stack using its current official upgrade procedure before rebuilding.

## Runtime verification

Run:

```bash
command -v tamarin-prover
command -v maude
command -v dot
tamarin-prover --version
tamarin-prover --help
maude --version
dot -V
tamarin-prover test
```

Then parse the bundled smoke theory from the skill package root:

```bash
tamarin-prover --parse-only assets/theory-template.spthy
```

Run precomputation only after Maude is verified:

```bash
tamarin-prover --quit-on-warning --precompute-only assets/theory-template.spthy
```

A usable installation resolves the intended binaries, prints the pinned Tamarin version, passes the installation self-test, parses the theory without diagnostics, and completes precomputation without well-formedness warnings.

## Interactive and remote use

Local interactive mode:

```bash
tamarin-prover interactive model.spthy
```

Open `http://127.0.0.1:3001`. The server loads `.spthy` files in the theory directory; start it from a directory whose models are intended for disclosure through that interface.

For a trusted remote host, bind the GUI to the remote loopback and forward port 3001:

```bash
ssh -L 3001:localhost:3001 SERVERNAME
```

Start Tamarin in a persistent terminal multiplexer on the server, then open `http://127.0.0.1:3001` locally. Do not expose the proof server on a public interface.

## Editor support

The official VS Code extension provides syntax highlighting, parser diagnostics, and well-formedness checks. Editor feedback complements but does not replace `--parse-only`, `--precompute-only`, or proof execution with the pinned binary.
