# Installation and runner selection

## Pin an executable, not a moving installer

Baseline: [v0.2.89](https://github.com/nektos/act/releases/tag/v0.2.89), source commit `4f411281417e88660bea1c1a1749aa71ae0bd60f`. Refresh the [latest release](https://github.com/nektos/act/releases/latest) when installing; distinguish stable/prerelease and preserve repository version policy. Compare `act --version` with the selected release.

| Environment | Supported installation route |
| --- | --- |
| Linux/macOS Homebrew | `brew install act` |
| Windows WinGet | `winget install nektos.act` |
| Windows Chocolatey / Scoop | `choco install act-cli` / `scoop install act` |
| Other hosts / exact version | matching OS/architecture release archive; verify SHA-256 before extracting |
| GitHub CLI integration | `gh extension install https://github.com/nektos/gh-act`, then `gh act` |

Package-manager installs may lag releases. Do not mix extension/binary versions accidentally. The official curl-to-sudo-bash installer is a trust/privilege decision; prefer an inspected installer or pinned archive rather than executing moving remote code as root.

For Linux x86_64 v0.2.89, the release archive is `act_Linux_x86_64.tar.gz`; its SHA-256 is `0191d6f1f3b716b5c55820032605d05fc3c1cdbf581ebeff655019e5dd1524c0`. Download archive and checksums from the **same tag**, verify the relevant entry, extract into an owned tools directory, and use its full path or project-owned PATH entry. Select Darwin arm64/x86_64 or Windows zip assets for those hosts; do not infer architecture from the workflow runner label.

Source builds require the pinned source's [go.mod](https://github.com/nektos/act/blob/4f411281417e88660bea1c1a1749aa71ae0bd60f/go.mod) and dependency toolchain requirements: its Go directive is 1.25.0, not the old 1.18/1.20 requirements still printed in docs/README. Follow the versioned Makefile/build metadata when compiling; a source binary's version string alone is insufficient revision evidence.

## Engine access

Container execution uses the Docker Engine API. On Linux, provision Docker Engine; on macOS/Windows, use an appropriate Docker Desktop engine. Verify daemon access (`docker version`, `docker info`) using the same identity/socket as act. Permission denied is not a reason to chmod the daemon socket world-writable or run unreviewed workflows with sudo.

`DOCKER_HOST` selects local/remote API endpoints, including unix and SSH endpoints. Docker's current context is not respected automatically. For an approved Docker context:

```bash
export DOCKER_HOST="$(docker context inspect --format '{{.Endpoints.docker.Host}}')"
```

Set the matching certificate policy when needed. A remote daemon changes filesystem/network assumptions: bind sources are on the daemon host, not necessarily the CLI machine.

`--container-daemon-socket=-` disables mounting the daemon socket **into** job containers. It does not remove act's own need for an engine. The Docker API socket confers broad control over the daemon/its host; expose it only for reviewed Docker-building/container actions.

Podman has a Docker-compatible API and the guide shows `DOCKER_HOST=unix:///.../podman.sock`, but explicitly states Podman/other backends are not officially supported. Use an existing approved socket for an experimental smoke, record backend/version, and avoid claiming Docker equivalence. Don't replace the consumer's engine without scope approval.

## Images, labels, and architecture

`-P runner-label=image` selects an image for the exact workflow label. Map each selected label, including matrix-expanded labels. Example:

```bash
act push -W .github/workflows/ci.yml -P ubuntu-22.04=catthehacker/ubuntu:act-22.04
```

The first-run Micro/Medium/Large survey writes configuration; use explicit mappings for automation. Small Node images are intentionally incomplete and often lack git, bash, compilers, Python, or SDKs. The guide's Node 16/Debian examples are historical recipes, not a current toolchain guarantee. `catthehacker/ubuntu:act-*` and `full-*` are third-party images with different installed tools and large disk costs. Inspect the toolchain inside the actual digest, or build a reviewed image with needed tools.

A Linux container is not a macOS/Windows runner. For those native jobs, execute on a capable corresponding host using `-P macos-latest=-self-hosted` or `-P windows-latest=-self-hosted`. This removes isolation; it neither provisions tools nor supplies a GitHub-hosted filesystem. JavaScript actions require Node on PATH even on the host.

On arm64, prefer compatible multiarch images/actions. If the workflow requires x86_64, use `--container-architecture=linux/amd64` with working engine emulation and accept its slower/different behavior. Do not use architecture flags to disguise an unavailable native OS/SDK.

## Workspace and state

- Default local workspace copying respects gitignore. If a required generated/ignored file is absent, inspect the copy boundary before disabling `--use-gitignore`; that can copy secret/private files.
- `--bind` mounts the working tree instead of copying it: commands can change the checkout, and remote engine paths/SELinux labels must be valid. Prefer disposable workspaces for proofs.
- `--reuse` retains containers/state. A warm run cannot prove clean setup; failed runs may retain resources unless `--rm` is selected.
- `--pull=false` uses an existing image rather than refreshing it; `--rebuild=false` separately controls Docker action rebuilds. Keep stale-image/action diagnosis focused.
- `--action-offline-mode` reuses cached actions/images but fetches missing ones; it is not a network-denial control or action pinning policy.

Sources: [installation](https://nektosact.com/installation/index.html), [runners](https://nektosact.com/usage/runners.html), [custom engine](https://nektosact.com/usage/custom_engine.html), [Docker context](https://nektosact.com/missing_functionality/docker_context.html), [pinned CLI flags](https://github.com/nektos/act/blob/4f411281417e88660bea1c1a1749aa71ae0bd60f/cmd/root.go).
