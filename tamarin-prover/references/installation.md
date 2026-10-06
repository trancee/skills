# Installation and runtime

## Refresh gate

REFRESH [install guide](https://tamarin-prover.com/install.html), [latest release/assets](https://github.com/tamarin-prover/tamarin-prover/releases/latest), and selected release notes before host changes.

RECORD version, origin, OS/architecture, dependency compatibility. Baseline: 1.12.0@82780bbaf3328a45f624ddb41e51bf75425f851c (2026-03-07), Maude supported through 3.5.1. Recheck selected release; not a universal future range.

## Select one installation route

### Homebrew on macOS or Linux

```bash
brew install tamarin-prover/tap/tamarin-prover
```

USE packaged Maude/Graphviz dependencies; record resolved formula version.

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

RUN inside WSL2/Ubuntu, not native Windows. Windows files: `/mnt/c/...`; interactive browser URL: `http://127.0.0.1:3001`.

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

Source builds compile many Haskell dependencies. Stack update failure -> current official upgrade procedure, then rebuild.

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

GATE: intended binaries/version; self-test passes; theory parses; precomputation has no well-formedness warnings.

## Interactive and remote use

Local interactive mode:

```bash
tamarin-prover interactive model.spthy
```

OPEN `http://127.0.0.1:3001`. Server loads theories in the model directory; expose only intended models.

For a trusted remote host, bind the GUI to the remote loopback and forward port 3001:

```bash
ssh -L 3001:localhost:3001 SERVERNAME
```

RUN in a persistent server terminal; open local loopback URL. No public proof-server bind.

## Editor support

VS Code extension: highlighting/parser/well-formedness feedback; not a replacement for pinned CLI/proof execution.
