---
name: zensical
description: "Installs, configures, builds, previews, and troubleshoots Zensical documentation sites. Use for zensical.toml or mkdocs.yml configuration, navigation and Markdown features, theme customization, MkDocs/Material migration, and static-site publishing workflows. Don't use for general documentation writing, unrelated static-site generators, or implementing Zensical internals."
compatibility: "Zensical 0.0.74 baseline; Python 3.11+ with pip or uv and a supported platform wheel. Browser needed for rendered-site verification. Docker is an optional build/preview route. uv symlink installation mode is unsupported. Hosting requires a separate static-site service."
metadata:
  category: "documentation"
  source: "https://zensical.org/docs/get-started/"
  sourceVersion: "zensical/zensical v0.0.74@1b51ddc27903c947fbcb807f6d1337d17930c0fc; zensical/docs@1a8b4b27db1ba939f85ed9381448c5c2004d19d7"
  createdBy: "github-copilot/gpt-6.1-sol"
  createdAt: "2026-11-01T13:01:43+01:00"
  updatedBy: "github-copilot/gpt-6.1-sol"
  updatedAt: "2026-11-01T13:01:43+01:00"
---

# Zensical

## Step 1: Establish the site contract

1. DEFINE install | new site | configuration/authoring feature | MkDocs migration | preview/build failure | static publishing | offline distribution.
2. IDENTIFY the repository's config/dependency/CI owners, Python environment, Zensical version, docs_dir/site_dir, navigation, Markdown extensions, plugins, overrides and target URL. Preserve existing package manager and configuration conventions.
3. READ the current [getting started](https://zensical.org/docs/get-started/) guide and [release](https://github.com/zensical/zensical/releases/latest); compare [source](https://github.com/zensical/zensical) when docs lag. Treat 0.0.74 as a tested alpha baseline, not a forever compatibility guarantee. Route documentation structure/prose to `diataxis`; keep this skill focused on the site generator.
4. For MkDocs/Material migration, READ [migration](references/migration.md) before modifying dependencies or config. Audit every required plugin: unsupported MkDocs plugins are silently ignored, not executed.

Completion: exact site/environment, requested rendered behavior and required migration/publishing boundaries are known.

## Step 2: Install in the owning environment

1. USE the existing project environment. For a new pip-managed environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install "zensical==0.0.74"
.venv/bin/zensical --version
```

On Windows, use `python -m venv .venv`, then `.venv/Scripts/python.exe -m pip install "zensical==0.0.74"` and `.venv/Scripts/zensical.exe --version`; activation is optional when using explicit executable paths. Substitute the researched version and preserve the project's pin/lock policy.
2. For an existing uv project, RUN `uv add --dev "zensical==0.0.74"` and invoke through `uv run zensical`. Use uv init only for a genuinely new Python project. Keep the resolved lockfile and Python requirement; avoid uv's unsupported symlink link mode.
3. INSPECT `zensical --help`, `zensical new --help`, `zensical build --help` and `zensical serve --help` in that environment. The supported commands are new/build/serve; do not invent MkDocs flags or gh-deploy.
4. VERIFY Python and supported wheel availability before selecting source compilation. Normal package installation does not require manually installing Rust or independently overriding the pinned zensical-ui dependency. Docker is optional; read the [official image](https://hub.docker.com/r/zensical/zensical) contract before choosing mount/entrypoint flags.

Completion: the intended environment reports the selected Zensical version and real command help; no global/site environment mismatch remains.

## Step 3: Create or configure the site

1. For a new site, RUN `zensical new <site-directory>` in the intended parent directory. Existing zensical.toml causes an error and other existing generated-target files are left untouched. Inspect generated files before integration: new also creates a GitHub Pages publishing workflow.
2. For an existing site, EDIT its configuration and sources directly; do not bootstrap a second config owner or overwrite unrelated CI. Keep mkdocs.yml during migration evaluation; TOML conversion is optional.
3. READ [configuration and authoring](references/configuration.md) for paths, navigation, Markdown, theme/JS, validation, watch or cache changes. Set site_name, the actual site_url, and separate relative docs_dir/site_dir. Internal links point to Markdown source paths and anchors.
4. For a small new-site example, COPY [TOML config](assets/zensical.toml) to zensical.toml, [home](assets/index.md) and [guide](assets/guide.md) to docs/index.md and docs/guide.md, and [CSS](assets/extra.css) to docs/stylesheets/extra.css. Replace the sample identity/URL before deploying. For YAML migration rehearsal, use [MkDocs config](assets/mkdocs.yml) in a disposable copy of that sample; it selects classic appearance and a native redirect.
5. ENABLE only requested extensions/plugins/customization. A successful config load does not prove plugin output, CSS behavior or browser-only rendering. Keep drafts and secrets out of production output; not_in_nav only hides automatic navigation.

Completion: one intentional configuration owner resolves sources, navigation, assets and requested feature options correctly.

## Step 4: Build and verify actual behavior

RUN through the selected environment, adding `-f <configuration>` when the config location could be ambiguous:

```sh
zensical build --clean --strict
zensical serve -a 127.0.0.1:8000
```

1. CONFIRM a clean strict build succeeds and inspect the actual site_dir output: expected HTML paths, canonical/sitemap prefix, local assets and published-page boundaries. --clean clears build cache; --strict must not be bypassed to silence broken links.
2. For a new validation gate, introduce one disposable broken page/anchor link, prove build --strict exits nonzero, repair it and prove the same command succeeds. Keep this in a temporary fixture, not production content.
3. OPEN the served site in a browser. Exercise home/deep navigation, source anchor links, search, selected Markdown features, stylesheet/JS behavior and mobile layout where changed. After editing a source page, verify live preview reloads the visible content; a build-only check is not UI proof.
4. For draft/exclude configuration, compare preview and production: drafts are available by URL in preview but omitted from build; exclude_docs is omitted in both. Inspect output/search entries rather than trusting a missing sidebar item.
5. For migrations, compare the representative baseline from the migration reference, including every required plugin/override/redirect and URL path. Unsupported essential behavior is a blocking prerequisite, not an accepted silent downgrade.
6. Stop the preview service and close the temporary browser tab after verification. serve is a local development server, not hosting. In 0.0.74, serve --strict is exposed but explicitly unsupported; use build --strict for the gate.

Completion: exact generated pages and rendered interactions pass, invalid links fail the gate, and requested migration/publication boundaries have observable evidence.

## Step 5: Prepare or execute publishing

1. If publishing/CI/offline output is requested, READ [publishing](references/publishing.md). Build in the pinned environment, run necessary generators first, and publish only site_dir through the approved static host.
2. INSPECT new's generated workflow before enabling it; preserve repository action pins, protected deploy branch and least-privilege permissions. Separate PR validation from deployment. Use --clean in CI per current upstream guidance; dependency caches are distinct from Zensical build cache.
3. Publish or change account/repository visibility/settings only when the exact target/action is authorized. A configured workflow is not an executed deployment; report whichever was actually exercised.

Completion: requested artifact/CI/deployment behavior matches the authorized scope; no preview server or unverified output is presented as production-ready hosting.

## Step 6: Report verification

COPY [verification report](assets/verification-report.md) structure and fill versions/config owner, commands/results, rendered evidence, plugin compatibility, output exclusions and deployment state. Mark unexercised host/offline/browser paths explicitly. Remove disposable fixtures; keep only production sources and intentional reusable assets.

## Error Handling

- Executable/import/theme missing -> confirm the project environment, selected wheel/Python and dependency pair; replace unsupported uv symlink installation with a supported mode.
- Missing config/site_name/docs directory -> inspect the chosen config/path owner; do not create a parallel config to mask the error.
- Broken link/anchor -> fix source-relative target and actual heading; run strict build again, without disabling validation.
- Unexpected missing feature after migration -> inspect the plugin support/options and output; unsupported config may be silently ignored even in strict mode.
- Stale build/preview -> reproduce with build --clean, then inspect watch roots and symlink targets; keep watch scope narrow.
- Unsupported CLI option -> read installed command help; use documented config properties or static-host pipeline instead.
- Missing migration prerequisite -> preserve the existing working production path and report the exact incompatible plugin/template behavior; no fake replacement or silent coverage reduction.
